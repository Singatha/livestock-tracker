import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

_request_id = ContextVar("request_id", default="-")
_request_id_pattern = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_structured_fields = (
    "event",
    "http_method",
    "http_path",
    "status_code",
    "duration_ms",
    "task_name",
    "task_id",
    "error",
)


def current_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            request = getattr(record, "request", None)
            record.request_id = getattr(request, "request_id", current_request_id())
        return True


class SuppressHealthcheckErrorsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request = getattr(record, "request", None)
        is_readiness_failure = (
            record.name == "django.request"
            and getattr(record, "status_code", None) == 503
            and getattr(request, "path", "") in {"/healthz/", "/readyz/"}
        )
        return not is_readiness_failure


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(
            timespec="milliseconds"
        )
        payload = {
            "timestamp": timestamp.replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", current_request_id()),
        }
        for field in _structured_fields:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("flockwise.request")

    def __call__(self, request):
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_request_id
            if _request_id_pattern.fullmatch(supplied_request_id)
            else uuid.uuid4().hex
        )
        request.request_id = request_id
        token = _request_id.set(request_id)
        started = time.monotonic()
        try:
            response = self.get_response(request)
            duration_ms = round((time.monotonic() - started) * 1000, 2)
            response["X-Request-ID"] = request_id
            self.logger.info(
                "request.complete",
                extra={
                    "event": "http.request.complete",
                    "http_method": request.method,
                    "http_path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except Exception:
            duration_ms = round((time.monotonic() - started) * 1000, 2)
            self.logger.exception(
                "request.failed",
                extra={
                    "event": "http.request.failed",
                    "http_method": request.method,
                    "http_path": request.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            _request_id.reset(token)
