from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.common.email import send_templated_email


class Command(BaseCommand):
    help = "Send a transactional email to verify the configured email backend."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Email address that should receive the test message.")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        try:
            validate_email(recipient)
        except ValidationError as exc:
            raise CommandError("Enter a valid recipient email address.") from exc
        sent = send_templated_email(
            subject="Flockwise email configuration test",
            recipient=recipient,
            template_name="test_email",
            context={},
        )
        if sent != 1:
            raise CommandError("The email backend did not confirm delivery.")
        self.stdout.write(self.style.SUCCESS(f"Test email accepted for {recipient}."))
