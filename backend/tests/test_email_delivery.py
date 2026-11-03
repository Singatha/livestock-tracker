from io import StringIO

import pytest
from django.core import mail
from django.core.management import CommandError, call_command


def test_send_test_email_command_sends_multipart_message(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    stdout = StringIO()

    call_command("send_test_email", "owner@example.com", stdout=stdout)

    assert "Test email accepted" in stdout.getvalue()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["owner@example.com"]
    assert mail.outbox[0].alternatives[0].mimetype == "text/html"


def test_send_test_email_command_rejects_invalid_recipient():
    with pytest.raises(CommandError, match="valid recipient"):
        call_command("send_test_email", "not-an-email")
