"""Bounded LRU cache for the TTS microservice.

Same semantics as the in-process ``_LruTtsCache`` in
``translator_api.providers.tts.edge``. Process-local; swap for redis when
running multiple replicas.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict


class TtsLruCache:
    def __init__(self, maxsize: int = 100) -> None:
        self._data: "OrderedDict[str, bytes]" = OrderedDict()
        self._maxsize = maxsize

    @staticmethod
    def _key(text: str, voice: str, rate: str, pitch: str) -> str:
        h = hashlib.sha256()
        h.update(text.encode("utf-8"))
        h.update(b"\x00")
        h.update(voice.encode("utf-8"))
        h.update(b"\x00")
        h.update(rate.encode("utf-8"))
        h.update(b"\x00")
        h.update(pitch.encode("utf-8"))
        return h.hexdigest()

    def get(self, text: str, voice: str, rate: str, pitch: str) -> bytes | None:
        key = self._key(text, voice, rate, pitch)
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, text: str, voice: str, rate: str, pitch: str, value: bytes) -> None:
        key = self._key(text, voice, rate, pitch)
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self._maxsize:
            self._data.popitem(last=False)

    def stats(self) -> dict[str, int]:
        return {"size": len(self._data), "maxsize": self._maxsize}
