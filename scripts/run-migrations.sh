#!/bin/sh
set -e

echo "Running migrations for database: ${DATABASE__NAME:-answer_hub}@${DATABASE__HOST:-localhost}"
poetry run alembic -c alembic.ini -n main upgrade head

test_db="${TEST_DATABASE__NAME:-answer_hub_test}"
if [ "${MIGRATE_TEST_DATABASE:-1}" = "1" ] && [ "$test_db" != "${DATABASE__NAME:-answer_hub}" ]; then
  echo "Running migrations for database: ${test_db}@${DATABASE__HOST:-localhost}"
  DATABASE__NAME="$test_db" poetry run alembic -c alembic.ini -n main upgrade head
fi

echo "Migrations completed successfully!"
