from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

EMAIL_TASK_RETRY_OPTIONS = {
    "autoretry_for": (SMTPException, OSError),
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "max_retries": 5,
    "ignore_result": True,
}


def send_templated_email(
    *,
    subject: str,
    recipient: str,
    template_name: str,
    context: dict,
) -> int:
    text_body = render_to_string(f"email/{template_name}.txt", context)
    html_body = render_to_string(f"email/{template_name}.html", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html_body, "text/html")
    return message.send(fail_silently=False)
