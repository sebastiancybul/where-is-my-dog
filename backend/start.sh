#!/usr/bin/env bash
set -o errexit

psql "${DATABASE_URL}" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
python manage.py migrate --noinput
python manage.py createsuperuser --noinput || true
python manage.py collectstatic --noinput
daphne -b 0.0.0.0 -p "${PORT:-8000}" config.asgi:application
