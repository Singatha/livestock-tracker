import logging
import os

from celery import Celery
from celery.signals import task_failure

logger = logging.getLogger("flockwise.celery")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("livestock_tracker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    logger.error(
        "celery.task_failed",
        extra={
            "event": "celery.task.failed",
            "task_name": getattr(sender, "name", str(sender)),
            "task_id": task_id,
            "error": repr(exception),
        },
    )
