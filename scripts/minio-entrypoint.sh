#!/bin/sh
set -eu

bucket="${S3__BUCKET:-cv-files}"

minio server /data --console-address ":9001" &
minio_pid=$!

until curl -sf "http://localhost:9000/minio/health/live" >/dev/null; do
  sleep 1
done

mc alias set local "http://localhost:9000" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"
mc mb "local/${bucket}" --ignore-existing

wait "${minio_pid}"
