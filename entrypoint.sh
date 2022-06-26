#!/bin/sh

sleep 10

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate


gunicorn --bind 0.0.0.0:80 --workers 3 yandex_service.wsgi:application 

exec "$@"
