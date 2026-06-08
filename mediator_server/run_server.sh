#!/usr/bin/env bash
python manage.py migrate
python manage.py seed_sources
python manage.py runserver 127.0.0.1:8000
