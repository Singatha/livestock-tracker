import logging
import uuid
from contextlib import suppress

from django.conf import settings
from django.core.cache import cache
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

    cache_key = f"flockwise:readiness:{uuid.uuid4().hex}"
    cache_value = "ok"
    cache_was_written = False
    try:
        cache.set(cache_key, cache_value, timeout=5)
        cache_was_written = True
        if cache.get(cache_key) != cache_value:
            raise RuntimeError("cache read-after-write failed")
        checks["cache"] = "ok"
    except Exception as exc:
        checks["cache"] = "unavailable"
        logger.warning(
            "readiness.cache_unavailable",
            extra={"event": "health.cache.unavailable", "error": repr(exc)},
        )
    finally:
        if cache_was_written:
            with suppress(Exception):
                cache.delete(cache_key)

    ready = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if ready else "unavailable", "checks": checks},
        status=200 if ready else 503,
    )


def healthcheck(request):
    return readiness(request)
