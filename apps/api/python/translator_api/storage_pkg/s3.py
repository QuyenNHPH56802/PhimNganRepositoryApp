"""S3-compatible storage via boto3."""

from __future__ import annotations

from datetime import datetime, timezone

import boto3
from botocore.client import Config

from translator_api.settings import get_settings
from translator_api.storage_pkg.base import ObjectHead, StorageError


class S3CompatibleStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )

    def upload(self, key: str, data: bytes, *, mime: str) -> str:
        try:
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=mime)
        except Exception as exc:
            raise StorageError(str(exc)) from exc
        return key

    def download(self, key: str) -> bytes:
        try:
            obj = self._client.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def download_to_path(self, key: str, path: str) -> None:
        try:
            self._client.download_file(self._bucket, key, path)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def presign_put(self, key: str, *, mime: str, expires_in: int) -> dict:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": mime},
            ExpiresIn=expires_in,
        )
        return {"key": key, "url": url, "headers": {"Content-Type": mime}, "expires_in": expires_in}

    def presign_get(self, key: str, *, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def head(self, key: str) -> ObjectHead | None:
        try:
            obj = self._client.head_object(Bucket=self._bucket, Key=key)
        except Exception:
            return None
        last_modified = obj.get("LastModified")
        if last_modified is not None and last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)
        return ObjectHead(
            key=key,
            size=int(obj.get("ContentLength", 0)),
            content_type=obj.get("ContentType"),
            etag=obj.get("ETag"),
            last_modified=last_modified,
        )