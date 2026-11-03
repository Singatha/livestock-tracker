from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import User
from apps.farms.models import FarmMembership
from apps.husbandry.models import HusbandryTask
from apps.notifications.models import Notification
from apps.notifications.services import generate_task_reminders
from apps.notifications.tasks import send_notification_email

pytestmark = pytest.mark.django_db


def farm_headers(farm):
    return {"HTTP_X_FARM_ID": str(farm.id)}


def test_generates_one_reminder_per_active_member_and_is_idempotent(farm, user):
    worker = User.objects.create_user(username="worker")
    inactive = User.objects.create_user(username="inactive")
    FarmMembership.objects.create(farm=farm, user=worker, role="worker")
    FarmMembership.objects.create(farm=farm, user=inactive, role="worker", is_active=False)
    HusbandryTask.objects.create(
        farm=farm,
        task_type="vaccination",
        title="Annual vaccination",
        due_date=timezone.localdate() + timedelta(days=2),
        reminder_days_before=3,
    )

    assert generate_task_reminders() == 2
    assert generate_task_reminders() == 0
    assert set(Notification.objects.values_list("recipient_id", flat=True)) == {user.id, worker.id}


def test_notifications_are_personal_and_farm_scoped(api_client, farm, user):
    HusbandryTask.objects.create(
        farm=farm,
        task_type="shearing",
        title="Shearing",
        due_date=timezone.localdate(),
    )
    generate_task_reminders()

    response = api_client.get("/api/v1/notifications/", **farm_headers(farm))
    assert response.status_code == 200
    assert response.data["count"] == 1
    notification_id = response.data["results"][0]["id"]

    mark_response = api_client.post(
        f"/api/v1/notifications/{notification_id}/mark-read/", {}, **farm_headers(farm)
    )
    assert mark_response.status_code == 200
    assert mark_response.data["is_read"] is True


def test_completing_task_resolves_unread_notifications(api_client, farm):
    task = HusbandryTask.objects.create(
        farm=farm,
        task_type="hoof_care",
        title="Trim hooves",
        due_date=timezone.localdate(),
    )
    generate_task_reminders()
    response = api_client.post(
        f"/api/v1/husbandry/tasks/{task.id}/complete/", {}, format="json", **farm_headers(farm)
    )
    assert response.status_code == 200
    assert not Notification.objects.filter(task=task, read_at__isnull=True).exists()


def test_task_reminder_email_includes_application_link(farm, user, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.FRONTEND_BASE_URL = "https://flockwise.example.com"
    user.email = "owner@example.com"
    user.save(update_fields=["email"])
    task = HusbandryTask.objects.create(
        farm=farm,
        task_type="vaccination",
        title="Annual vaccination",
        due_date=timezone.localdate(),
    )
    generate_task_reminders()
    notification = Notification.objects.get(task=task, recipient=user)

    send_notification_email.run(str(notification.id))

    assert len(mail.outbox) == 1
    assert "https://flockwise.example.com/tasks" in mail.outbox[0].body
    assert mail.outbox[0].alternatives[0].mimetype == "text/html"
