#!/usr/bin/env bash
# Backup Translator Postgres + object store.
#
# Required environment (.env.prod):
#   POSTGRES_HOST=postgres
#   POSTGRES_PORT=5432
#   POSTGRES_USER=translator
#   POSTGRES_PASSWORD=...
#   POSTGRES_DB=translator
#   BACKUP_TARGET=s3
#   S3_ENDPOINT=http://minio:9000
#   S3_ACCESS_KEY=...
#   S3_SECRET_KEY=...
#   S3_BUCKET=translator-backups
#   BACKUP_KEEP_DAYS=30
#
# Outputs to ./backups/<UTC-timestamp>/ and uploads that prefix to S3.

set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="./backups/${TS}"
mkdir -p "${OUT}"

echo "[backup] ${TS}"
echo "[backup] dump postgres -> ${OUT}/postgres.sql.gz"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST:-postgres}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-translator}" \
    -d "${POSTGRES_DB:-translator}" \
    -Fc \
    | gzip -9 > "${OUT}/postgres.sql.gz"

if [[ "${BACKUP_TARGET:-s3}" == "s3" ]]; then
    python - "${OUT}" "${TS}" <<'PY'
import os, sys, hashlib, pathlib
import boto3

out, ts = sys.argv[1], sys.argv[2]
endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
bucket = os.environ.get("S3_BUCKET", "translator-backups")
client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
)

for path in pathlib.Path(out).rglob("*"):
    if path.is_dir():
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    key = f"{ts}/{path.relative_to(out).as_posix()}"
    client.upload_file(str(path), bucket, key)
    client.put_object(Bucket=bucket, Key=f"{key}.sha256", Body=digest.encode("utf-8"))
    print(f"[backup] uploaded {key} sha256={digest[:12]}")
PY
fi

if [[ -n "${BACKUP_KEEP_DAYS:-}" ]]; then
    find ./backups -mindepth 1 -maxdepth 1 -type d -mtime "+${BACKUP_KEEP_DAYS}" -exec rm -rf {} +
fi

echo "[backup] done"