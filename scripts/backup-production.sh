#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=${ENV_FILE:-"$PROJECT_ROOT/.env.production"}
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
BACKUP_ROOT=${BACKUP_ROOT:-"$PROJECT_ROOT/backups"}
STAGING_ROOT="$PROJECT_ROOT/backups"

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing $ENV_FILE. Copy .env.production.example and configure it first." >&2
    exit 1
fi

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="$BACKUP_ROOT/$timestamp"
mkdir -p "$BACKUP_ROOT" "$STAGING_ROOT"
if ! mkdir "$destination"; then
    echo "Backup destination already exists: $destination" >&2
    exit 1
fi

archive="attachments-$timestamp-$$.tar.gz"
cleanup_archive() {
    rm -f "$STAGING_ROOT/$archive"
}
trap cleanup_archive EXIT INT TERM

echo "Backing up PostgreSQL..."
compose exec -T db sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "$destination/database.dump"

echo "Backing up attachments..."
compose --profile tools run --rm -T \
    -e BACKUP_ARCHIVE="$archive" maintenance \
    sh -c 'tar -czf "/backups/$BACKUP_ARCHIVE" -C /data .'
mv "$STAGING_ROOT/$archive" "$destination/attachments.tar.gz"

if command -v sha256sum >/dev/null 2>&1; then
    (cd "$destination" && sha256sum database.dump attachments.tar.gz > SHA256SUMS)
else
    (cd "$destination" && shasum -a 256 database.dump attachments.tar.gz > SHA256SUMS)
fi

echo "Backup complete: $destination"
