import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.common.email import EMAIL_TASK_RETRY_OPTIONS, send_templated_email

from .models import User

logger = logging.getLogger("flockwise.email")


@shared_task(**EMAIL_TASK_RETRY_OPTIONS)
def send_password_reset_email(email: str) -> None:
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password/{uid}/{token}"
    send_templated_email(
        subject="Reset your Flockwise password",
        recipient=user.email,
        template_name="password_reset",
        context={"reset_url": reset_url},
    )
    logger.info("email.sent", extra={"event": "email.password_reset.sent"})
