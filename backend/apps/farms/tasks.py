import logging

from celery import shared_task
from django.conf import settings

from apps.common.email import EMAIL_TASK_RETRY_OPTIONS, send_templated_email

from .models import FarmInvitation

logger = logging.getLogger("flockwise.email")


@shared_task(**EMAIL_TASK_RETRY_OPTIONS)
def send_farm_invitation_email(invitation_id: str) -> None:
    invitation = FarmInvitation.objects.select_related("farm").filter(id=invitation_id).first()
    if (
        invitation is None
        or invitation.status != FarmInvitation.Status.PENDING
        or invitation.is_expired
    ):
        return

    invitation_url = f"{settings.FRONTEND_BASE_URL}/invitations/{invitation.token}"
    send_templated_email(
        subject=f"Invitation to {invitation.farm.name}",
        recipient=invitation.email,
        template_name="farm_invitation",
        context={
            "farm_name": invitation.farm.name,
            "role": invitation.get_role_display(),
            "invitation_url": invitation_url,
            "expires_at": invitation.expires_at,
        },
    )
    logger.info("email.sent", extra={"event": "email.farm_invitation.sent"})
