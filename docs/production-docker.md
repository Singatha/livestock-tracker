# Private Production Docker Deployment

This deployment is intended for a personal, single-host Flockwise installation. It uses immutable application images, PostgreSQL and attachment volumes, Gunicorn, Nuxt's production server, Celery, Redis, and Caddy. It does not require Kubernetes or cloud services.

## Prerequisites

- Docker Engine or Docker Desktop with Compose v2
- At least 2 GB of available memory
- A copy of this repository on the host
- A hostname only if access beyond `localhost` or automatic HTTPS is required

## First Start

```bash
cp .env.production.example .env.production
```

Replace both `change-me` values. Generate a Django key with a password manager or:

```bash
openssl rand -base64 48
```

Validate and start the stack:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Open `http://localhost`. Only Caddy publishes host ports; PostgreSQL, Redis, Django, and Nuxt remain on the internal Docker network.

Create the first administrative account:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec api \
  python manage.py createsuperuser
```

## HTTPS and LAN Access

For localhost-only use, keep `SITE_ADDRESS=:80` and the HTTP security settings from the example file. For a real DNS hostname, set:

```dotenv
SITE_ADDRESS=flockwise.example.net
DJANGO_ALLOWED_HOSTS=flockwise.example.net
DJANGO_CORS_ALLOWED_ORIGINS=https://flockwise.example.net
DJANGO_CSRF_TRUSTED_ORIGINS=https://flockwise.example.net
FRONTEND_BASE_URL=https://flockwise.example.net
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
DJANGO_SECURE_HSTS_SECONDS=31536000
```

Caddy will request and renew certificates when the hostname resolves to the host and ports 80/443 are reachable. For LAN access without public DNS, use an appropriate local certificate or VPN; do not enable secure-cookie settings while serving plain HTTP.

## Transactional Email

The example uses the console backend, which writes messages to container logs. Configure SMTP before relying on password recovery, invitations, or reminder email, then send a test message:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec api \
  python manage.py send_test_email you@example.com
```

See [Transactional Email](email-delivery.md) for encryption settings, background retry behavior, and domain deliverability requirements.

## Routine Operations

View health and logs:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f --tail=200
curl --fail http://localhost/livez/
curl --fail http://localhost/readyz/
```

Production application logs default to JSON. See [Observability and Health Checks](observability.md) for request correlation, readiness semantics, optional Sentry configuration, and alert guidance.

Authentication and invitation throttles use Redis database 1 by default, separate from Celery's database 0. Keep `DJANGO_NUM_PROXIES=1` for the supplied Caddy topology. Review [Production Security](security.md) before making the service reachable beyond a trusted network.

Stop without deleting data:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

Never add `-v` unless intentionally deleting the database, attachments, and Caddy state.

## Backups

The backup script creates a timestamped PostgreSQL custom dump, attachment archive, and checksums:

```bash
./scripts/backup-production.sh
```

Backups are written under `backups/` and ignored by Git. Copy them to another disk; a backup stored only beside the live Docker volumes does not protect against disk failure. Test restoration periodically.

Restore a selected backup:

```bash
./scripts/restore-production.sh backups/20261103T120000Z
```

Restore is destructive and requires typing `RESTORE`. It stops application services, replaces the database and attachments, then restarts the stack.

Rehearse the complete backup and restore process without touching the normal production project:

```bash
./scripts/rehearse-restore.sh
```

The rehearsal creates a uniquely named Compose project and temporary backup directory, changes database and attachment markers after backup, restores them, verifies their original values, and removes its containers and volumes. Run it after changing Docker, PostgreSQL, or maintenance scripts and periodically as part of operational checks. CI also runs this rehearsal for every pull request and push to `main`.

## Upgrade Procedure

1. Create and copy a fresh backup off-host.
2. Pull or check out the desired application revision.
3. Validate the rendered configuration.
4. Rebuild and restart application services.
5. Check container health, logs, login, and one read/write workflow.

```bash
./scripts/backup-production.sh
git pull --ff-only
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

The API container applies migrations before Gunicorn starts. Do not run two versions concurrently during a schema upgrade.

## Rollback

If no irreversible migration or write occurred, check out the previous revision and rebuild. If data changed or the migration is not backward-compatible, restore the pre-upgrade backup with the matching application revision. Keep the `.env.production` file outside version control.

## Security Notes

- Use strong, unique Django and PostgreSQL secrets.
- Do not publish ports 5432, 6379, 8000, or 3000.
- Keep Docker, base images, and dependencies updated.
- Keep the Redis-backed throttle cache private and use the exact trusted-proxy count.
- Configure and verify SMTP if invitation, reminder, or password-reset email is needed.
- Review logs and backup results regularly.
- This setup is single-host; availability depends on that host and its storage.
