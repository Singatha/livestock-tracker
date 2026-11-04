<div align="center">
  <img src="frontend/public/icons/app-icon.svg" alt="Flockwise logo" width="96" height="96">
  <h1>Flockwise</h1>
  <p>A modern livestock management platform for healthier animals and better-informed farm operations.</p>

  ![Django](https://img.shields.io/badge/Django-5.2-075f38?logo=django&logoColor=white)
  ![Nuxt](https://img.shields.io/badge/Nuxt-4-00DC82?logo=nuxt&logoColor=white)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
</div>

## About

Flockwise helps sheep and goat farmers manage livestock records from one responsive workspace. It combines individual animal histories with farm-level health, reproduction, growth, medicine, nutrition, task, and reporting workflows. The web interface is installable as a Progressive Web App (PWA).

## Features

- Farms, team memberships, role-based access, flocks, and animal profiles
- Health observations, treatments, attachments, and complete animal timelines
- Breeding records, expected birth dates, and birth outcomes
- Weight history, average daily gain, and growth reporting
- Medicine products, batches, treatment courses, doses, and withdrawal periods
- Feed products, diet plans, husbandry tasks, reminders, and notifications
- CSV reports and imports, audit history, and private farm documents
- Signup, session authentication, password recovery, and installable PWA support

## Architecture

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Web | Nuxt 4, Vue 3, TypeScript, Tailwind CSS | Responsive user interface and PWA |
| API | Django 5.2, Django REST Framework | Authentication, permissions, and business workflows |
| Data | PostgreSQL 17 | Relational livestock and farm records |
| Jobs | Celery, Redis | Scheduled reminders and background processing |
| Local runtime | Docker Compose | Reproducible development environment |

The backend is a modular monolith. Domain modules live in `backend/apps/`, while the frontend is organised under `frontend/app/`. Architecture decisions and MVP boundaries are documented in `docs/adr/` and `docs/mvp.md`.

## Quick Start

### Requirements

- Docker Desktop with Docker Compose
- Git

### Run locally

```bash
git clone <repository-url>
cd livestock-tracker-platform
cp .env.example .env
docker compose up --build
```

Open the following services:

- Web application: http://localhost:3000
- API: http://localhost:8000/api/v1/
- OpenAPI documentation: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/

Create an account from `/signup`, or create an admin user with:

```bash
docker compose exec api python manage.py createsuperuser
```

To load a dashboard-ready demonstration farm, run:

```bash
docker compose exec api python manage.py seed_demo_data
```

Sign in with `demo` / `demo-password`. The command is safe to rerun and accepts
`--username` and `--password` when different local credentials are preferred.

Stop the stack with `docker compose down`. Avoid `docker compose down -v` unless you intentionally want to delete local database and attachment volumes.

## Configuration

Copy `.env.example` and replace the development defaults. Important settings include:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Cryptographic signing key; use a long random value |
| `POSTGRES_PASSWORD` | Local or deployed database password |
| `DJANGO_ALLOWED_HOSTS` | Hosts accepted by Django |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Trusted frontend origins |
| `NUXT_PUBLIC_API_BASE` | Browser-visible API base URL |
| `DJANGO_ATTACHMENT_MAX_SIZE` | Maximum upload size in bytes |
| `DJANGO_CACHE_URL` / `DJANGO_NUM_PROXIES` | Shared throttling cache and trusted reverse-proxy count |
| `DJANGO_THROTTLE_*` | Scoped authentication and invitation request limits |
| `DJANGO_LOG_FORMAT` / `DJANGO_LOG_LEVEL` | Application log structure and severity threshold |
| `SENTRY_DSN` | Optional Django and Celery error reporting; empty disables it |
| `DJANGO_EMAIL_*` | SMTP delivery, encryption mode, credentials, and timeout |
| `FRONTEND_BASE_URL` | Base URL used in emailed links |

The console email backend is suitable for local development; reset and invitation links appear in API or worker logs. Never commit `.env` or production credentials.

## Testing and Quality

Run checks through the active Compose stack:

```bash
docker compose exec api ruff check .
docker compose exec api ruff format --check .
docker compose exec api pytest -q
docker compose exec web npm run typecheck
docker compose exec web npm run build
```

Backend tests cover permissions, farm isolation, validation, and API workflows. New domain behavior should include focused `test_*.py` coverage.

GitHub Actions runs these checks for pull requests and `main`, validates both production Compose profiles, rehearses database and attachment recovery, and builds the production images. Semantic-version tags publish multi-architecture API and web images to GitHub Container Registry. See [Continuous Integration and Releases](docs/ci-cd.md).

## PWA Preview

Service workers are disabled during development to prevent stale caches. Test the production PWA locally with:

```bash
docker compose stop web
docker compose run --rm web npm run build
docker compose run --rm --service-ports web npm run preview -- --host=0.0.0.0
```

Open http://localhost:3000 and use the account menu or browser installation control. Farm API responses and private media are deliberately excluded from offline caching.

## Production Deployment

For a self-contained installation, use the hardened Compose stack with Gunicorn, Nuxt's production server, Caddy, health checks, persistent volumes, and backup tooling. See [Private Production Docker Deployment](docs/production-docker.md).

For public cloud deployment with managed PostgreSQL, Redis, private object storage, immutable registry images, and automatic HTTPS, see [Cloud Production Deployment](docs/cloud-deployment.md).

Health endpoints, request IDs, JSON logs, alert guidance, and optional Sentry configuration are documented in [Observability and Health Checks](docs/observability.md).

Password resets, farm invitations, and task reminders support retrying background delivery through a provider-neutral SMTP configuration. See [Transactional Email](docs/email-delivery.md).

## Roadmap

- Optional OAuth providers
- Location tracking when compatible livestock tags are available
- Native mobile applications if PWA usage demonstrates a clear need
- Livestock knowledge assistant after the core operational product is mature

## Contributing

Read [AGENTS.md](AGENTS.md) for repository structure, coding standards, testing expectations, and pull-request guidance. Keep changes focused, include tests for new backend behavior, and include screenshots for visible UI changes.

## Security

Do not report sensitive vulnerabilities through a public issue. Share them privately with the repository owner. Review [Production Security](docs/security.md) before exposing the service and retain HTTPS, secure settings, private infrastructure, monitoring, and tested backups.

## License

No open-source license has been selected. Unless a license is added, all rights are reserved by the repository owner.
