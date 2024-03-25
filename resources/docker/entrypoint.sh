#!/bin/sh

python manage.py makemigrations
python manage.py migrate
python manage.py createcachetable

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    python manage.py createsuperuser --noinput
fi

exec "$@"