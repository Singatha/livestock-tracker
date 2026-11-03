#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 backups/YYYYMMDDTHHMMSSZ" >&2
    exit 1
fi

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=${ENV_FILE:-"$PROJECT_ROOT/.env.production"}
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
backup_dir=$(CDPATH= cd -- "$1" 2>/dev/null && pwd) || {
    echo "Backup directory not found: $1" >&2
    exit 1
}

for file in database.dump attachments.tar.gz; do
    if [ ! -f "$backup_dir/$file" ]; then
        echo "Missing $backup_dir/$file" >&2
        exit 1
    fi
done

if [ -f "$backup_dir/SHA256SUMS" ]; then
    echo "Verifying backup checksums..."
    if command -v sha256sum >/dev/null 2>&1; then
        (cd "$backup_dir" && sha256sum -c SHA256SUMS)
    else
        (cd "$backup_dir" && shasum -a 256 -c SHA256SUMS)
    fi
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing $ENV_FILE." >&2
    exit 1
fi

printf 'This replaces the current database and attachments. Type RESTORE to continue: '
read -r confirmation
if [ "$confirmation" != "RESTORE" ]; then
    echo "Restore cancelled."
    exit 1
fi

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

echo "Stopping application services..."
compose stop proxy web beat worker api

echo "Restoring PostgreSQL..."
compose exec -T db sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore --clean --if-exists --no-owner --exit-on-error -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < "$backup_dir/database.dump"

echo "Restoring attachments..."
cp "$backup_dir/attachments.tar.gz" "$PROJECT_ROOT/backups/restore-attachments.tar.gz"
compose --profile tools run --rm -T \
    -e RESTORE_ARCHIVE=restore-attachments.tar.gz maintenance \
    sh -c 'find /data -mindepth 1 -delete && tar -xzf "/backups/$RESTORE_ARCHIVE" -C /data'
rm "$PROJECT_ROOT/backups/restore-attachments.tar.gz"

echo "Starting application services..."
compose up -d
echo "Restore complete."
