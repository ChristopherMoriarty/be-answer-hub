#!/bin/sh
set -e

DB_URL="postgresql://${DATABASE__USER}:${DATABASE__PASSWORD}@${DATABASE__HOST}:${DATABASE__PORT}"

echo "Running migrations with URL: ${DB_URL}"

export MAIN_URL="${DB_URL}/${DATABASE__NAME}"
sed -i "s|^sqlalchemy.url = .*|sqlalchemy.url = ${MAIN_URL}|" alembic.ini
poetry run alembic -c alembic.ini -n main upgrade head

echo "Migrations completed successfully!"
