from unittest.mock import Mock, patch

import pytest
from django.db import OperationalError


@pytest.mark.django_db
@patch("config.views.Redis.from_url")
def test_healthcheck_reports_dependency_availability(redis_from_url, client):
    redis_from_url.return_value = Mock()

    response = client.get("/healthz/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }


def test_liveness_does_not_require_dependencies(client):
    response = client.get("/livez/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
@patch("config.views.Redis.from_url")
def test_readiness_reports_redis_failure(redis_from_url, client):
    redis_from_url.side_effect = ConnectionError("redis unavailable")

    response = client.get("/readyz/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "ok", "redis": "unavailable"},
    }


@patch("config.views.Redis.from_url")
@patch("config.views.connection.cursor")
def test_readiness_reports_database_failure(cursor, redis_from_url, client):
    cursor.side_effect = OperationalError("database unavailable")
    redis_from_url.return_value = Mock()

    response = client.get("/readyz/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "unavailable", "redis": "ok"},
    }
