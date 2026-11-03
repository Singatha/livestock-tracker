import json
import logging
import re

from config.observability import JsonFormatter


def test_response_contains_generated_request_id(client):
    response = client.get("/livez/")

    assert re.fullmatch(r"[0-9a-f]{32}", response["X-Request-ID"])


def test_valid_request_id_is_preserved(client):
    response = client.get("/livez/", headers={"X-Request-ID": "client-request_123"})

    assert response["X-Request-ID"] == "client-request_123"


def test_invalid_request_id_is_replaced(client):
    response = client.get("/livez/", headers={"X-Request-ID": "invalid request id\n"})

    assert response["X-Request-ID"] != "invalid request id\n"
    assert re.fullmatch(r"[0-9a-f]{32}", response["X-Request-ID"])


def test_json_formatter_emits_structured_fields():
    record = logging.LogRecord(
        name="flockwise.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request.complete",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.event = "http.request.complete"
    record.status_code = 200

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "request.complete"
    assert payload["request_id"] == "request-123"
    assert payload["event"] == "http.request.complete"
    assert payload["status_code"] == 200
