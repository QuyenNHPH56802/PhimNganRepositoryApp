"""Local filesystem storage."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from translator_api.settings import get_settings
from translator_api.storage_pkg.base import ObjectHead, StorageError


class LocalStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self._root = Path(settings.local_storage_root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.lstrip("/").replace("..", "_")
        return self._root / safe_key

    def upload(self, key: str, data: bytes, *, mime: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_bytes(data)
        except OSError as exc:
            raise StorageError(str(exc)) from exc
        return key

    def download(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except OSError as exc:
            raise StorageError(str(exc)) from exc

    def download_to_path(self, key: str, path: str) -> None:
        data = self.download(key)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def presign_put(self, key: str, *, mime: str, expires_in: int) -> dict:
        return {"key": key, "url": f"file://{self._path(key)}", "headers": {"Content-Type": mime}, "expires_in": expires_in}

    def presign_get(self, key: str, *, expires_in: int) -> str:
        return f"file://{self._path(key)}"

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def head(self, key: str) -> ObjectHead | None:
        path = self._path(key)
        if not path.exists():
            return None
        stat = path.stat()
        return ObjectHead(
            key=key,
            size=stat.st_size,
            content_type=None,
            etag=None,
            last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )