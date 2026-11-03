from unittest.mock import Mock, patch

from config.celery import log_task_failure


@patch("config.celery.logger")
def test_task_failure_emits_structured_context(logger):
    sender = Mock(name="task")
    sender.name = "apps.notifications.tasks.send_notification_email"
    exception = RuntimeError("delivery failed")

    log_task_failure(sender=sender, task_id="task-123", exception=exception)

    logger.error.assert_called_once_with(
        "celery.task_failed",
        extra={
            "event": "celery.task.failed",
            "task_name": "apps.notifications.tasks.send_notification_email",
            "task_id": "task-123",
            "error": "RuntimeError('delivery failed')",
        },
    )
