#!/usr/bin/env bash
# Verify the most recent backup by downloading the SHA256 sidecar and
# comparing it against the recomputed hash. Exit non-zero on mismatch.

set -euo pipefail
TS="${BACKUP_TS:?set BACKUP_TS}"
BUCKET="${S3_BUCKET:?set S3_BUCKET}"
ENDPOINT="${S3_ENDPOINT:?set S3_ENDPOINT}"

python - "${TS}" "${BUCKET}" "${ENDPOINT}" <<'PY'
import os, sys, hashlib, pathlib
import boto3

ts, bucket, endpoint = sys.argv[1], sys.argv[2], sys.argv[3]
client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
)
mismatches = 0
checked = 0
for obj in client.list_objects_v2(Bucket=bucket, Prefix=ts).get("Contents", []):
    if not obj["Key"].endswith(".sha256"):
        continue
    sidecar_key = obj["Key"]
    target_key = sidecar_key[: -len(".sha256")]
    expected = client.get_object(Bucket=bucket, Key=sidecar_key)["Body"].read().decode().strip()
    body = client.get_object(Bucket=bucket, Key=target_key)["Body"].read()
    actual = hashlib.sha256(body).hexdigest()
    checked += 1
    if expected != actual:
        print(f"FAIL {target_key}: expected={expected} actual={actual}")
        mismatches += 1
    else:
        print(f"OK   {target_key}")
print(f"[backup_verify] checked={checked} mismatches={mismatches}")
sys.exit(1 if mismatches else 0)
PY