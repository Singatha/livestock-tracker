# End-to-End Testing

Playwright exercises Flockwise through the browser against production API and web images. The suite currently verifies owner sign-in, animal registration and task scheduling, a farm-scoped CSV export, and the worker permission boundary for team management.

## Run Locally

Install the browser once after `npm ci`:

```bash
cd frontend
npx playwright install chromium
cd ..
./scripts/run-e2e.sh
```

The runner creates an isolated Compose project on ports `3100` and `8100`, applies migrations, and loads repeatable demo data. Its test-only defaults are `e2e-owner` / `e2e-password-2026`; override them with `E2E_USERNAME` and `E2E_PASSWORD`. Containers and anonymous volumes are removed after the run, so development data is untouched.

Set `E2E_KEEP_STACK=1` when debugging to leave the stack running. Then use `cd frontend && npm run test:e2e:ui`, or inspect the last HTML report with `npm run test:e2e:report`. Stop the retained stack with:

```bash
docker compose -p flockwise-e2e -f docker-compose.e2e.yml down --volumes
```

## Test Design

Keep critical journeys in `frontend/tests/e2e/`. Locate controls by accessible role, label, or visible name so tests also enforce basic usability. Each test should assert a user-visible outcome rather than implementation details. Seed stable prerequisites centrally, generate unique records inside tests, and avoid depending on development data.

CI runs Chromium with one worker and retries failures twice. On retry it captures a trace; failures retain screenshots and video. The `playwright-report` workflow artifact contains the HTML report and raw test output for diagnosis.
