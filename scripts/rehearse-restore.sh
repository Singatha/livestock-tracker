#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
ENV_FILE=${ENV_FILE:-"$PROJECT_ROOT/.env.production.example"}
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/flockwise-restore.XXXXXX")

export COMPOSE_PROJECT_NAME="flockwise-restore-rehearsal-$$"
export ENV_FILE
export BACKUP_ROOT="$work_dir/backups"

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

cleanup() {
    compose down -v --remove-orphans >/dev/null 2>&1 || true
    if [ -d "$work_dir" ]; then
        rm -r "$work_dir"
    fi
}
trap cleanup EXIT INT TERM

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing $ENV_FILE." >&2
    exit 1
fi

mkdir -p "$BACKUP_ROOT"

echo "Starting an isolated PostgreSQL volume..."
compose up -d --wait db

echo "Creating database and attachment recovery markers..."
compose exec -T db sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE TABLE restore_probe (value text NOT NULL); INSERT INTO restore_probe VALUES ('\''before-backup'\'');"'
compose --profile tools run --rm -T maintenance \
    sh -c 'printf "%s\n" "before-backup" > /data/restore-probe.txt'

echo "Creating a backup with the production script..."
"$PROJECT_ROOT/scripts/backup-production.sh"
backup_dir=$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -print -quit)
if [ -z "$backup_dir" ]; then
    echo "The backup script did not create a backup directory." >&2
    exit 1
fi

echo "Changing both recovery markers after the backup..."
compose exec -T db sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "UPDATE restore_probe SET value = '\''after-backup'\'';"'
compose --profile tools run --rm -T maintenance \
    sh -c 'printf "%s\n" "after-backup" > /data/restore-probe.txt'

echo "Restoring the isolated volumes with the production script..."
printf 'RESTORE\n' | RESTORE_RESTART_SERVICES=false \
    "$PROJECT_ROOT/scripts/restore-production.sh" "$backup_dir"

database_value=$(compose exec -T db sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" psql -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT value FROM restore_probe;"')
attachment_value=$(compose --profile tools run --rm -T maintenance \
    sh -c 'cat /data/restore-probe.txt')

if [ "$database_value" != "before-backup" ]; then
    echo "Database restore verification failed: $database_value" >&2
    exit 1
fi
if [ "$attachment_value" != "before-backup" ]; then
    echo "Attachment restore verification failed: $attachment_value" >&2
    exit 1
fi

echo "Restore rehearsal passed: database and attachment contents were recovered."
