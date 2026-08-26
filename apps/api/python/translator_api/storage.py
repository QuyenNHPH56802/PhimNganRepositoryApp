"""Storage abstraction. Phase 1 implements S3-compatible presigned URL helper.
The MinIO local dev bucket is used as the default target; production will
swap to a managed S3-compatible deployment per docs/licenses.md."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import Config

from translator_api.settings import get_settings


def make_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
    )


def build_object_key(project_id: uuid.UUID, asset_id: uuid.UUID, filename: str) -> str:
    safe = filename.replace("..", "_").replace("/", "_")
    return f"projects/{project_id}/assets/{asset_id}/raw/{datetime.now(timezone.utc):%Y%m%d}/{safe}"


def presign_upload(project_id: uuid.UUID, asset_id: uuid.UUID, filename: str, mime: str) -> dict:
    settings = get_settings()
    key = build_object_key(project_id, asset_id, filename)
    expires_in = 3600
    client = make_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": mime},
        ExpiresIn=expires_in,
    )
    return {
        "key": key,
        "url": url,
        "headers": {"Content-Type": mime},
        "expires_in": expires_in,
    }