#!/bin/sh

echo "Waiting for PostgreSQL (db:5432) and Redis (redis:6379)..."
while ! nc -z db 5432 || ! nc -z redis 6379; do
  sleep 1
done

echo "PostgreSQL and Redis are ready"


echo "Applying initial migrations and collecting static..."
cd ./app || true
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

if [ "$(echo "$GENERATE_INITIAL_DATA" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    echo "Generating initial data..."
    python ./fixtures/generate_initial_data.py
    python manage.py loaddata ./fixtures/initial_data.json
else
    echo "Skipping initial data generation (GENERATE_INITIAL_DATA=false)"
fi

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL"
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME');
user.set_password('$DJANGO_SUPERUSER_PASSWORD');
user.save();
"
fi

echo "Starting gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 event_calendar.wsgi:application