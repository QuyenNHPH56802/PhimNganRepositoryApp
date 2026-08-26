"""Phase 6 cache-aware activities.

These wrap provider invocations with `ArtifactCache.lookup` / `store`. If
the artifact for `(kind, project, asset, model_version, config_hash)`
already exists, the worker reuses it instead of calling the provider again.
"""

from __future__ import annotations

import hashlib
import os
from typing import Callable

from temporalio import activity

from translator_api.providers.base import ProviderContext
from translator_api.providers.registry import PROVIDER_REGISTRY
from translator_api.storage_pkg.cache import ArtifactCache, CacheEntry
from translator_api.storage_pkg.s3 import S3CompatibleStorage
from translator_worker.deps import build_storage, get_redis_client


def _hash_config(config: dict) -> str:
    return hashlib.sha256(repr(sorted(config.items())).encode("utf-8")).hexdigest()[:16]


async def _artifact_cache() -> ArtifactCache:
    redis = await get_redis_client()
    return ArtifactCache(redis=redis, storage=build_storage())


@activity.defn(name="cache_lookup")
async def cache_lookup(kind: str, project_id: str, asset_id: str, model_version: str, config: dict) -> dict:
    cache = await _artifact_cache()
    fingerprint = ArtifactCache.fingerprint(
        kind=kind,
        project_id=project_id,
        asset_id=asset_id,
        model_version=model_version,
        config_hash=_hash_config(config),
    )
    entry = await cache.lookup(fingerprint=fingerprint)
    return {"fingerprint": fingerprint, "entry": entry.__dict__ if entry else None}


@activity.defn(name="cache_store")
async def cache_store(kind: str, project_id: str, asset_id: str, model_version: str, config: dict, payload: bytes, provider_id: str) -> dict:
    cache = await _artifact_cache()
    fingerprint = ArtifactCache.fingerprint(
        kind=kind,
        project_id=project_id,
        asset_id=asset_id,
        model_version=model_version,
        config_hash=_hash_config(config),
    )
    entry = await cache.store(
        fingerprint=fingerprint,
        payload=payload,
        provider_id=provider_id,
        model_version=model_version,
    )
    return entry.__dict__