#!/usr/bin/env bash
set -e

coverage run --source='.' --omit='./venv/*,./main_page/migrations/*,./manage.py,*__init__.py,./key.py,./main_page/libs/server_config.py,./clairvoyance/*,main_page/tests*' manage.py test main_page.tests
coverage xml