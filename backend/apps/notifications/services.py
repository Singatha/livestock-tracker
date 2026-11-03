from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.farms.models import FarmMembership
from apps.husbandry.models import HusbandryTask

from .models import Notification


@transaction.atomic
def generate_task_reminders(*, today=None) -> int:
    today = today or timezone.localdate()
    tasks = HusbandryTask.objects.filter(
        status=HusbandryTask.Status.SCHEDULED,
        due_date__lte=today + timedelta(days=30),
    ).select_related("farm", "animal")
    created_count = 0
    for task in tasks:
        reminder_date = task.due_date - timedelta(days=task.reminder_days_before)
        if today < reminder_date:
            continue
        kind = (
            Notification.Kind.TASK_OVERDUE if task.due_date < today else Notification.Kind.TASK_DUE
        )
        recipients = FarmMembership.objects.filter(farm=task.farm, is_active=True).values_list(
            "user_id", flat=True
        )
        for recipient_id in recipients:
            subject = task.animal.ear_tag if task.animal else task.farm.name
            timing = "Overdue" if kind == Notification.Kind.TASK_OVERDUE else "Upcoming"
            notification, created = Notification.objects.get_or_create(
                recipient_id=recipient_id,
                task=task,
                kind=kind,
                defaults={
                    "farm": task.farm,
                    "title": f"{timing}: {task.title}",
                    "message": f"{subject} · due {task.due_date:%d %b %Y}",
                    "link": f"/animals/{task.animal_id}" if task.animal_id else "/tasks",
                },
            )
            created_count += int(created)
            if created and notification.recipient.email:
                from .tasks import send_notification_email

                transaction.on_commit(
                    lambda notification_id=notification.id: send_notification_email.delay(
                        str(notification_id)
                    )
                )
    return created_count


def deliver_notification_email(notification_id: str) -> None:
    from apps.common.email import send_templated_email

    notification = Notification.objects.select_related("recipient").get(id=notification_id)
    send_templated_email(
        subject=notification.title,
        recipient=notification.recipient.email,
        template_name="task_reminder",
        context={
            "title": notification.title,
            "message": notification.message,
            "task_url": f"{settings.FRONTEND_BASE_URL}{notification.link}",
        },
    )
