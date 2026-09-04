"""Phase 6 cache-aware activities.

These wrap provider invocations with `ArtifactCache.lookup` / `store`. If
the artifact for `(kind, project, asset, model_version, config_hash)`
already exists, the worker reuses it instead of calling the provider again.
"""

from __future__ import annotations

import hashlib

from temporalio import activity

from translator_api.storage_pkg.cache import ArtifactCache
from translator_worker.deps import build_storage, get_redis_client


# TTL policies by artifact type (in seconds)
CACHE_TTL_POLICIES = {
    "asr": 7 * 24 * 3600,           # 7 days - expensive GPU operation
    "translation": 3 * 24 * 3600,   # 3 days - LLM API calls
    "tts": 24 * 3600,               # 1 day - can regenerate quickly
    "subtitle": 12 * 3600,          # 12 hours - cheap operation
    "alignment": 3 * 24 * 3600,     # 3 days - moderate cost
    "diarization": 5 * 24 * 3600,   # 5 days - GPU operation
    "separation": 2 * 24 * 3600,    # 2 days - audio processing
}

DEFAULT_CACHE_TTL = 24 * 3600  # 1 day default


def _hash_config(config: dict) -> str:
    return hashlib.sha256(repr(sorted(config.items())).encode("utf-8")).hexdigest()[:16]


def _get_cache_ttl(kind: str) -> int:
    """Get TTL for artifact type, with fallback to default."""
    return CACHE_TTL_POLICIES.get(kind, DEFAULT_CACHE_TTL)


async def _artifact_cache(kind: str) -> ArtifactCache:
    """Create cache instance with TTL appropriate for artifact type."""
    redis = await get_redis_client()
    ttl = _get_cache_ttl(kind)
    return ArtifactCache(redis=redis, storage=build_storage(), ttl_seconds=ttl)


@activity.defn(name="cache_lookup")
async def cache_lookup(kind: str, project_id: str, asset_id: str, model_version: str, config: dict) -> dict:
    """Lookup cached artifact by fingerprint.
    
    Args:
        kind: Artifact type (asr, translation, tts, etc.) - determines TTL policy
    """
    cache = await _artifact_cache(kind)
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
    """Store artifact in cache with TTL based on artifact type.
    
    Args:
        kind: Artifact type (asr, translation, tts, etc.) - determines TTL policy
            - asr: 7 days (expensive GPU operation)
            - translation: 3 days (LLM API calls)
            - tts: 1 day (can regenerate quickly)
            - subtitle: 12 hours (cheap operation)
    
    Returns:
        Cache entry with storage_key and TTL used
    """
    cache = await _artifact_cache(kind)
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
    
    ttl = _get_cache_ttl(kind)
    activity.logger.info(
        "cache_store: kind=%s fingerprint=%s ttl=%ds (%dh)", 
        kind, fingerprint[:8], ttl, ttl // 3600
    )
    
    return entry.__dict__
