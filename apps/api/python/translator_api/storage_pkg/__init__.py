"""Storage abstraction.

Two implementations ship today:
- S3CompatibleStorage (boto3) for MinIO in dev and any S3-compatible backend
  in production. Used for presigned URLs and large object I/O.
- LocalStorage for dev/test runs that skip MinIO and write to a local path.

Both honor StorageProviderId from translator_shared.providers.
"""

from __future__ import annotations

from translator_api.storage_pkg.base import ObjectHead, Storage, StorageError
from translator_api.storage_pkg.cache import ArtifactCache, CacheEntry
from translator_api.storage_pkg.local import LocalStorage
from translator_api.storage_pkg.s3 import S3CompatibleStorage

__all__ = [
    "ArtifactCache",
    "CacheEntry",
    "LocalStorage",
    "ObjectHead",
    "S3CompatibleStorage",
    "Storage",
    "StorageError",
]
