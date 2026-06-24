#!/bin/sh
set -e

echo "Running migrations for database: ${DATABASE__NAME:-answer_hub}@${DATABASE__HOST:-localhost}"

poetry run alembic -c alembic.ini -n main upgrade head

echo "Migrations completed successfully!"
