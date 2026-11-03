#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    python manage.py migrate --noinput
fi

if [ "$#" -eq 0 ]; then
    set -- python manage.py runserver 0.0.0.0:8000
fi

exec "$@"
