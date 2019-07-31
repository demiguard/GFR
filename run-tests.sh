#!/usr/bin/env bash
set -e

# Check arg count
if [ $# -gt 1 ]; then
  echo "Error: To many arguments, expected one."
  exit 1
fi

# Verbose option
if [ "$1" == "-v" ]; then
  coverage run --source='.' --omit='./venv/*,./main_page/migrations/*,./manage.py,*__init__.py,./key.py,./main_page/libs/server_config.py,./clairvoyance/*,main_page/tests*' manage.py test -v 2 main_page.tests
else
  coverage run --source='.' --omit='./venv/*,./main_page/migrations/*,./manage.py,*__init__.py,./key.py,./main_page/libs/server_config.py,./clairvoyance/*,main_page/tests*' manage.py test main_page.tests
fi

# Generate report in xml format
coverage xml