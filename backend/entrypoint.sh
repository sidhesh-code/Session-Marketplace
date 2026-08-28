#!/bin/sh
set -e

# Extract DB host and port from environment variables (local Docker or Railway)
DB_HOST="${POSTGRES_HOST:-${PGHOST:-}}"
DB_PORT="${POSTGRES_PORT:-${PGPORT:-5432}}"

if [ -n "$DB_HOST" ]; then
  echo "Waiting for PostgreSQL database at $DB_HOST:$DB_PORT..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
  echo "PostgreSQL is reachable!"
fi

echo "Applying database migrations..."
python manage.py makemigrations accounts sessions_app bookings --noinput
python manage.py migrate --noinput

echo "Seeding demo sessions data if empty..."
python manage.py seed_demo_data

echo "Starting Gunicorn / Django application..."
exec "$@"
