#!/bin/sh
set -e

echo "Waiting for PostgreSQL database at $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 1
done

echo "PostgreSQL is reachable!"

echo "Applying database migrations..."
python manage.py makemigrations accounts sessions_app bookings --noinput
python manage.py migrate --noinput

echo "Starting Gunicorn / Django application..."
exec "$@"
