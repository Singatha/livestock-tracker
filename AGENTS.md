# Repository Guidelines

## Project Structure

- `backend/`: Django 5.2 modular monolith and REST API.
- `backend/apps/`: business modules such as accounts, farms, animals, and dashboard.
- `frontend/`: Nuxt 4, Vue 3, and TypeScript web application.
- `docs/adr/`: accepted architecture decisions.
- `docs/mvp.md`: current product scope and deferred features.
- `docker-compose.yml`: local PostgreSQL, API, and web orchestration.

## Development Commands

Run backend commands from `backend/`:

- `.venv/bin/python manage.py migrate`: apply database migrations.
- `.venv/bin/python manage.py runserver`: start the API locally.
- `.venv/bin/pytest`: run backend tests.
- `.venv/bin/ruff check .`: lint Python.
- `.venv/bin/ruff format --check .`: verify Python formatting.

Run frontend commands from `frontend/`:

- `npm run dev`: start Nuxt locally.
- `npm run typecheck`: validate Vue and TypeScript types.
- `npm run build`: create the production bundle.
- `npm run test:e2e`: run Playwright against an already running test stack.

Use `docker compose up --build` from the repository root to start the complete stack.
Use `./scripts/run-e2e.sh` to build an isolated production-like stack, seed it, and run the critical browser journeys.

## Code and Architecture Standards

Use four-space indentation and type hints in Python. Keep HTTP concerns in DRF views and serializers, multi-step writes in services, and complex reads in selectors. Every farm-owned query must be scoped through an authenticated, active farm membership. Do not introduce new deployment units without measured operational need.

Vue components use TypeScript, `<script setup>`, and `PascalCase` filenames. Keep server data in API composables rather than duplicating it in global client state. Design screens mobile-first and preserve accessible labels, keyboard behavior, and meaningful empty states.

## Testing and Contributions

Name Python tests `test_*.py`. Cover permissions, farm isolation, domain constraints, and API outcomes for every workflow. Add Vitest tests for frontend logic and Playwright tests for critical user journeys. Prefer accessible role and label locators over CSS selectors.

Use concise imperative commit subjects. Pull requests should explain behavior changes, list verification commands, identify schema or environment changes, and include screenshots for visible UI updates. Never commit `.env`, virtual environments, database files, `node_modules`, or build output.
