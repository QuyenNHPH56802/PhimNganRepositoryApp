"""Storage base types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class StorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class ObjectHead:
    key: str
    size: int
    content_type: str | None
    etag: str | None
    last_modified: datetime | None


class Storage(Protocol):
    def upload(self, key: str, data: bytes, *, mime: str) -> str: ...
    def download(self, key: str) -> bytes: ...
    def presign_put(self, key: str, *, mime: str, expires_in: int) -> dict: ...
    def presign_get(self, key: str, *, expires_in: int) -> str: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def head(self, key: str) -> ObjectHead | None: ...
    def download_to_path(self, key: str, path: str) -> None: ...