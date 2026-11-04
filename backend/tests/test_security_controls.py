from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle

from apps.common.checks import check_production_security

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def set_throttle_rates(monkeypatch, **rates):
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", rates)


def test_login_throttle_ignores_untrusted_forwarded_addresses(client, monkeypatch):
    set_throttle_rates(monkeypatch, login="2/min")
    monkeypatch.setattr(api_settings, "NUM_PROXIES", 0)
    payload = {"username": "unknown", "password": "incorrect"}

    first = client.post(
        "/api/v1/auth/login/",
        payload,
        content_type="application/json",
        HTTP_X_FORWARDED_FOR="198.51.100.1",
    )
    second = client.post(
        "/api/v1/auth/login/",
        payload,
        content_type="application/json",
        HTTP_X_FORWARDED_FOR="198.51.100.2",
    )
    limited = client.post(
        "/api/v1/auth/login/",
        payload,
        content_type="application/json",
        HTTP_X_FORWARDED_FOR="198.51.100.3",
    )

    assert first.status_code == 400
    assert second.status_code == 400
    assert limited.status_code == 429
    assert int(limited["Retry-After"]) > 0


@patch("apps.accounts.views.send_password_reset_email.delay")
def test_password_reset_is_rate_limited_without_revealing_accounts(delay, client, monkeypatch):
    set_throttle_rates(monkeypatch, password_reset="1/hour")
    payload = {"email": "unknown@example.com"}

    accepted = client.post("/api/v1/auth/password-reset/", payload, content_type="application/json")
    limited = client.post("/api/v1/auth/password-reset/", payload, content_type="application/json")

    assert accepted.status_code == 204
    assert limited.status_code == 429
    delay.assert_called_once_with("unknown@example.com")


def test_invitation_throttle_applies_only_to_posts(api_client, farm, monkeypatch):
    set_throttle_rates(monkeypatch, farm_invitations="1/hour")
    headers = {"HTTP_X_FARM_ID": str(farm.id)}

    assert api_client.get("/api/v1/farms/team/invitations/", **headers).status_code == 200
    assert api_client.get("/api/v1/farms/team/invitations/", **headers).status_code == 200
    invalid = api_client.post(
        "/api/v1/farms/team/invitations/",
        {"email": "invalid", "role": "worker"},
        format="json",
        **headers,
    )
    limited = api_client.post(
        "/api/v1/farms/team/invitations/",
        {"email": "invalid", "role": "worker"},
        format="json",
        **headers,
    )

    assert invalid.status_code == 400
    assert limited.status_code == 429


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "security-check-test",
        }
    },
    REST_FRAMEWORK={"NUM_PROXIES": 0},
)
def test_deployment_check_rejects_process_local_throttling():
    warning_ids = {warning.id for warning in check_production_security(None)}

    assert "flockwise.W001" in warning_ids
    assert "flockwise.W003" in warning_ids
