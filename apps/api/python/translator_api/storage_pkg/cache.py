"""Artifact cache layer.

Phase 6 wraps Redis (metadata) + S3 (payload) behind a single
`ArtifactCache` helper. The cache key is a fingerprint composed of
`(kind, project_id, asset_id, model_version, config_hash)`. Storing the
SHA-256 of the payload in Redis lets us dedupe hot path calls; the actual
artifact is referenced via a storage key.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol


class StorageClient(Protocol):
    def upload(self, key: str, payload: bytes, *, mime: str | None = None) -> str: ...
    def download(self, key: str) -> bytes: ...


class RedisClient(Protocol):
    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: bytes, ex: int | None = None) -> None: ...


@dataclass(frozen=True)
class CacheEntry:
    fingerprint: str
    storage_key: str
    provider_id: str
    model_version: str


class ArtifactCache:
    """Content-addressable cache."""

    def __init__(self, *, redis: RedisClient, storage: StorageClient, ttl_seconds: int = 60 * 86400) -> None:
        self._redis = redis
        self._storage = storage
        self._ttl = ttl_seconds

    @staticmethod
    def fingerprint(*, kind: str, project_id: str, asset_id: str, model_version: str, config_hash: str) -> str:
        digest = hashlib.sha256(f"{kind}|{project_id}|{asset_id}|{model_version}|{config_hash}".encode("utf-8")).hexdigest()
        return digest[:32]

    async def lookup(self, *, fingerprint: str) -> CacheEntry | None:
        raw = await self._redis.get(f"artifact:{fingerprint}")
        if raw is None:
            return None
        text = raw.decode("utf-8")
        parts = text.split("|")
        if len(parts) != 3:
            return None
        return CacheEntry(fingerprint=fingerprint, storage_key=parts[0], provider_id=parts[1], model_version=parts[2])

    async def store(self, *, fingerprint: str, payload: bytes, provider_id: str, model_version: str, mime: str = "application/octet-stream") -> CacheEntry:
        storage_key = f"cache/{fingerprint[:2]}/{fingerprint}"
        self._storage.upload(storage_key, payload, mime=mime)
        await self._redis.set(f"artifact:{fingerprint}", f"{storage_key}|{provider_id}|{model_version}".encode("utf-8"), ex=self._ttl)
        return CacheEntry(fingerprint=fingerprint, storage_key=storage_key, provider_id=provider_id, model_version=model_version)

    async def get_or_compute(self, *, fingerprint: str, compute: Callable[[], Awaitable[tuple[bytes, str, str]]], mime: str = "application/octet-stream") -> CacheEntry:
        cached = await self.lookup(fingerprint=fingerprint)
        if cached is not None:
            return cached
        payload, provider_id, model_version = await compute()
        return await self.store(fingerprint=fingerprint, payload=payload, provider_id=provider_id, model_version=model_version, mime=mime)
