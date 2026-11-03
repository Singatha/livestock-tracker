# Observability and Health Checks

Flockwise exposes lightweight operational signals without requiring a separate monitoring stack. Production application logs are structured JSON, API requests carry correlation IDs, and Sentry remains disabled unless configured.

## Health Endpoints

- `/livez/` returns `200` when the Django process can serve HTTP. It does not contact external services.
- `/readyz/` returns `200` only when PostgreSQL and Redis respond; otherwise it returns `503` with per-dependency status.
- `/healthz/` remains a backward-compatible alias for readiness.

Docker health checks use `/readyz/`. External uptime monitoring should check `/livez/` to distinguish an unavailable process from a dependency incident, while deployment systems should use `/readyz/` before routing traffic.

## Request Correlation

Every API response includes `X-Request-ID`. A client-supplied identifier is preserved only when it contains 1–128 letters, numbers, dots, underscores, or hyphens; otherwise the API generates a new identifier. Search this value in API logs when investigating a failed request.

Production JSON request events contain the request ID, method, path without query parameters, response status, and duration. Request bodies, user details, credentials, and farm data are not logged.

## Logging

Use `DJANGO_LOG_FORMAT=json` in production and `console` locally. `DJANGO_LOG_LEVEL` defaults to `INFO`. View recent events with:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail=200 api worker beat
```

HTTP requests emit `http.request.complete` or `http.request.failed`. Failed Celery tasks emit `celery.task.failed` with task name, ID, and exception representation. Caddy and container-runtime logs remain separate infrastructure streams.

## Optional Sentry

Leave `SENTRY_DSN` empty to disable Sentry. To enable it, configure:

```dotenv
SENTRY_DSN=https://public-key@your-sentry-host/project-id
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=flockwise@0.1.0
SENTRY_ERROR_SAMPLE_RATE=1.0
SENTRY_TRACES_SAMPLE_RATE=0.0
```

The integration covers Django and Celery errors, disables default personal-data collection, and does not send request bodies. Performance tracing is off by default; increase its sampling rate only after reviewing cost and privacy implications. Do not commit the DSN if the project treats it as a secret.

## Minimum Alerts

For a personal deployment, alert on repeated `/livez/` failures, sustained `/readyz/` failures, container restart loops, Celery task failures, and PostgreSQL backup failures. Add a full metrics stack only when operational history shows that logs and endpoint monitoring are insufficient.
