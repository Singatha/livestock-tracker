#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
compose_file="$repo_dir/docker-compose.e2e.yml"
project_name="${E2E_PROJECT_NAME:-flockwise-e2e}"
username="${E2E_USERNAME:-e2e-owner}"
password="${E2E_PASSWORD:-e2e-password-2026}"
exit_code=0

cleanup() {
  if [ "$exit_code" -ne 0 ]; then
    docker compose -p "$project_name" -f "$compose_file" logs --no-color api web || true
  fi
  if [ "${E2E_KEEP_STACK:-0}" != "1" ]; then
    docker compose -p "$project_name" -f "$compose_file" down --volumes --remove-orphans || true
  fi
}

trap 'exit_code=$?; cleanup; exit "$exit_code"' EXIT INT TERM

docker compose -p "$project_name" -f "$compose_file" up --detach --build --wait
docker compose -p "$project_name" -f "$compose_file" exec -T api \
  python manage.py seed_demo_data --username "$username" --password "$password"

cd "$repo_dir/frontend"
PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://127.0.0.1:3100}" \
E2E_USERNAME="$username" \
E2E_PASSWORD="$password" \
npm run test:e2e
