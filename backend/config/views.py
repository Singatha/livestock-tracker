import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from redis import Redis

logger = logging.getLogger("flockwise.health")


def liveness(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "unavailable"
        logger.warning(
            "readiness.database_unavailable",
            extra={"event": "health.database.unavailable", "error": repr(exc)},
        )

    redis_client = None
    try:
        redis_client = Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "unavailable"
        logger.warning(
            "readiness.redis_unavailable",
            extra={"event": "health.redis.unavailable", "error": repr(exc)},
        )
    finally:
        if redis_client is not None:
            redis_client.close()

    ready = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if ready else "unavailable", "checks": checks},
        status=200 if ready else 503,
    )


def healthcheck(request):
    return readiness(request)
