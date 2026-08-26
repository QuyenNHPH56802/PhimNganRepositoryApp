#!/usr/bin/env bash
# Restore Translator from a backup timestamp directory.
#
# Usage:
#   BACKUP_TS=20240101T000000Z ./scripts/restore.sh
#
# Required env:
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
#   S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET (when pulling from S3)

set -euo pipefail
TS="${BACKUP_TS:?set BACKUP_TS}"
TARGET="${BACKUP_DIR:-./backups/${TS}}"

if [[ ! -d "${TARGET}" ]]; then
    python - "${TS}" "${TARGET}" <<'PY'
import os, sys
import boto3
ts, target = sys.argv[1], sys.argv[2]
client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT"),
    aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
)
bucket = os.environ["S3_BUCKET"]
os.makedirs(target, exist_ok=True)
for obj in client.list_objects_v2(Bucket=bucket, Prefix=ts).get("Contents", []):
    if obj["Key"].endswith(".sha256"):
        continue
    rel = obj["Key"][len(ts) + 1:]
    out_path = os.path.join(target, rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    client.download_file(bucket, obj["Key"], out_path)
PY
fi

echo "[restore] dropping schema public"
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "[restore] loading ${TARGET}/postgres.sql.gz"
gunzip -c "${TARGET}/postgres.sql.gz" | PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

echo "[restore] done"