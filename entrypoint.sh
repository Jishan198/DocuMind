#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files for production..."
python manage.py collectstatic --noinput

echo "Starting Daphne server (Handling HTTP and WebSockets)..."
# Bind to 0.0.0.0 and port 8000
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
