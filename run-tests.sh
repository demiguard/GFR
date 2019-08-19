#!/usr/bin/env bash
set -e

# Check if help command should be ran
if [[ $# -eq 1 && ( "$1" == "-h" || "$1" == "--help" ) ]]; then
  echo "Help information:"
  echo "-h  --help        : displays this text"
  echo "-v  --verbose     : enable verbose mode for tests"
  echo "-s  --selenium    : only run selenium tests"
  echo "-ns --no-selenium : disable selenium tests"
  echo "-nr --no-report   : disable XML report generation"
  exit 0
fi

# Check if Selenium drivers are available
drivers=("./main_page/tests/selenium_drivers/geckodriver-0-24-0-x64")
run_selenium=0

for driver in ${drivers[*]}; do
  if !(test -f "$driver"); then
    echo "Warning: Missing Selenium driver: '$driver'"
    run_selenium=1
    break
  fi
done

# Check arguments and generate command to run
omit_str="./venv/*,./main_page/migrations/*,./manage.py,*__init__.py,./key.py,./main_page/libs/server_config.py,./clairvoyance/*,main_page/tests*"
base_test_cmd="coverage run --source='.' --omit='"

tests="main_page.tests.test_dataset_creator main_page.tests.test_formatting main_page.tests.test_clearance_math main_page.tests.test_dicomlib"
selenium_tests="main_page.tests.test_fill_study"
verbose=""
verbose_enabled=1
report=0

for var in "$@"; do
  if [[ "$var" == "-s" || "$var" == "--selenium" ]]; then  # Run ONLY the Selenium tests
    tests=""
  elif [[ "$var" == "-ns" || "$var" == "--no-selenium" ]]; then # Don't run Selenium tests
    selenium_tests=""
    run_selenium=2
  elif [[ "$var" == "-v" || "$var" == "--verbose" ]]; then # Whether or not to enable verbose mode
    verbose="-v 2"
    verbose_enabled=0
  elif [[ "$var" == "-nr" || "$var" == "--no-report" ]]; then # Whether or not to generated an XML report
    report=1
  else
    echo "Error: Got unknown argument: '$var'"
    exit 1
  fi
done

if [ "$verbose_enabled" -eq 0 ]; then
  if [ "$run_selenium" -eq 0 ]; then
    echo "Info: Selenium tests are enabled"
  elif [ "$run_selenium" -eq 2 ]; then # Manually disabled
    echo "Info: Selenium tests disabled"
  else
    echo "Info: Selenium tests disabled, due to missing driver"
  fi
fi

test_cmd="$base_test_cmd$omit_str' manage.py test $verbose $tests $selenium_tests"

# Run generated command
eval $test_cmd

# Generate report in XML format
if [ "$report" -eq 0 ]; then
  coverage xml
fi

exit 0