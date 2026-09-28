#!/bin/sh
set -e

if command -v alembic >/dev/null 2>&1; then
  run_alembic() { alembic "$@"; }
else
  run_alembic() { poetry run alembic "$@"; }
fi

echo "Running migrations for database: ${DATABASE__NAME:-answer_hub}@${DATABASE__HOST:-localhost}"
run_alembic -c alembic.ini -n main upgrade head

test_db="${TEST_DATABASE__NAME:-answer_hub_test}"
if [ "${MIGRATE_TEST_DATABASE:-1}" = "1" ] && [ "$test_db" != "${DATABASE__NAME:-answer_hub}" ]; then
  echo "Running migrations for database: ${test_db}@${DATABASE__HOST:-localhost}"
  DATABASE__NAME="$test_db" run_alembic -c alembic.ini -n main upgrade head
fi

echo "Migrations completed successfully!"
