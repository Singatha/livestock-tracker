# Transactional Email

Flockwise sends password resets, farm invitations, and task reminders as multipart text and HTML messages. HTTP requests queue delivery through Celery so a slow email provider does not hold open the user request. Transient SMTP and network failures retry up to five times with exponential backoff.

## Configuration

Local development uses Django's console backend and writes messages to API or worker logs. For production, configure an SMTP or transactional email provider:

```dotenv
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_DEFAULT_FROM_EMAIL=Flockwise <noreply@example.com>
DJANGO_EMAIL_HOST=smtp.example.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=provider-user
DJANGO_EMAIL_HOST_PASSWORD=provider-secret
DJANGO_EMAIL_USE_TLS=true
DJANGO_EMAIL_USE_SSL=false
DJANGO_EMAIL_TIMEOUT=10
FRONTEND_BASE_URL=https://flockwise.example.com
```

Use TLS with port 587 or SSL with port 465 according to the provider's instructions; never enable both settings. Store credentials only in the deployment environment or secret manager. `FRONTEND_BASE_URL` must be the public application origin so reset and invitation links work.

## Verify Delivery

After deployment, ask the configured backend to send a real message:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec api \
  python manage.py send_test_email you@example.com
```

The command confirms that the backend accepted the message, not that it reached the inbox. Check the provider activity log and recipient inbox. Configure SPF, DKIM, and DMARC for the sending domain before relying on email for account recovery.

Then verify one password reset, one farm invitation, and one task reminder. Watch worker logs for `email.*.sent`, `celery.task.failed`, authentication errors, or exhausted retries.

## Operational Notes

- Keep the Celery worker and Redis healthy; queued messages are delivered by the worker.
- A revoked or expired farm invitation is skipped if it has not already been sent.
- Password-reset requests always queue the same task whether or not the address exists, avoiding an account-discovery response difference.
- Rotate an exposed SMTP credential immediately and review provider activity.
