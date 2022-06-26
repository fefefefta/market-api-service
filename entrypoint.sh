#!/bin/bash

python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate

gunicorn --bind 0.0.0.0:80 --workers 3 market.wsgi:application
