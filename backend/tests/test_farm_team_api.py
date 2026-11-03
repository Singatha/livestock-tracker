from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.farms.models import FarmInvitation, FarmMembership, FarmMembershipAudit
from apps.farms.tasks import send_farm_invitation_email

pytestmark = pytest.mark.django_db


def headers(farm):
    return {"HTTP_X_FARM_ID": str(farm.id)}


@patch("apps.farms.team_services.send_farm_invitation_email.delay")
def test_owner_invites_member_and_records_audit(
    delay,
    api_client,
    farm,
    settings,
    django_capture_on_commit_callbacks,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            "/api/v1/farms/team/invitations/",
            {"email": "worker@example.com", "role": "worker"},
            format="json",
            **headers(farm),
        )
    assert response.status_code == 201
    delay.assert_called_once_with(str(response.data["id"]))

    send_farm_invitation_email.run(str(response.data["id"]))
    assert len(mail.outbox) == 1
    assert str(response.data["token"]) in mail.outbox[0].body
    assert mail.outbox[0].alternatives[0].mimetype == "text/html"
    assert FarmMembershipAudit.objects.filter(
        farm=farm, event_type=FarmMembershipAudit.EventType.INVITED
    ).exists()


def test_revoked_invitation_email_is_not_sent(farm, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    invitation = FarmInvitation.objects.create(
        farm=farm,
        email="worker@example.com",
        role=FarmMembership.Role.WORKER,
        expires_at=timezone.now() + timedelta(days=1),
        invited_by=farm.owner,
        status=FarmInvitation.Status.REVOKED,
    )

    send_farm_invitation_email.run(str(invitation.id))

    assert len(mail.outbox) == 0


def test_invitation_is_email_bound_and_can_be_accepted(farm, other_user):
    other_user.email = "worker@example.com"
    other_user.save(update_fields=["email"])
    invitation = FarmInvitation.objects.create(
        farm=farm,
        email=other_user.email,
        role=FarmMembership.Role.WORKER,
        expires_at=timezone.now() + timedelta(days=1),
        invited_by=farm.owner,
    )
    client = APIClient()
    client.force_login(other_user)
    response = client.post(
        "/api/v1/farms/invitations/accept/",
        {"token": str(invitation.token)},
        format="json",
    )
    assert response.status_code == 200
    assert FarmMembership.objects.filter(
        farm=farm, user=other_user, role=FarmMembership.Role.WORKER, is_active=True
    ).exists()


def test_manager_cannot_grant_owner_role(farm, other_user):
    other_user.email = "manager@example.com"
    other_user.save(update_fields=["email"])
    FarmMembership.objects.create(farm=farm, user=other_user, role=FarmMembership.Role.MANAGER)
    client = APIClient()
    client.force_login(other_user)
    response = client.post(
        "/api/v1/farms/team/invitations/",
        {"email": "new-owner@example.com", "role": "owner"},
        format="json",
        **headers(farm),
    )
    assert response.status_code == 403


def test_last_owner_cannot_be_demoted(api_client, farm, user):
    membership = FarmMembership.objects.get(farm=farm, user=user)
    response = api_client.patch(
        f"/api/v1/farms/team/members/{membership.id}/",
        {"role": "manager"},
        format="json",
        **headers(farm),
    )
    assert response.status_code == 400
    membership.refresh_from_db()
    assert membership.role == FarmMembership.Role.OWNER


def test_worker_cannot_view_team(farm, other_user):
    FarmMembership.objects.create(farm=farm, user=other_user, role=FarmMembership.Role.WORKER)
    client = APIClient()
    client.force_login(other_user)
    response = client.get("/api/v1/farms/team/members/", **headers(farm))
    assert response.status_code == 403
