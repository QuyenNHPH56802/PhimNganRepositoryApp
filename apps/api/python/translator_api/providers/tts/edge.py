"""Edge-TTS provider (free, no API key).

Edge-TTS taps the same neural speech service behind Microsoft Edge's
"Read Aloud" feature. It supports 322+ voices across 75 languages including
two Vietnamese neural voices:

- vi-VN-HoaiMyNeural (female)
- vi-VN-NamMinhNeural (male)

Following the pyVideoTrans pattern, Edge-TTS is the default fallback when
local GPU engines (VietVoice / CosyVoice) are unavailable. The provider
supports chunked synthesis by splitting text into sentence-aligned chunks
(<=500 chars) before dispatching to the underlying websocket stream.

Note: Edge-TTS streams MP3 by default; we wrap the resulting bytes in an
``audio/mpeg`` mime and rely on FFmpeg to decode downstream. The output
storage key is namespaced under ``tts/edge_tts/<voice>/<hex>.mp3``.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import os
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.tts.base import TtsInput
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_configs import TtsProviderConfig
from translator_shared.provider_responses_extra import TtsResponse

# Reference: https://github.com/jianchang512/pyvideotrans edge_tts channel
VOICE_MAP: dict[str, str] = {
    "vi-VN-HoaiMyNeural": "vi-VN-HoaiMyNeural",
    "vi-VN-NamMinhNeural": "vi-VN-NamMinhNeural",
    "vi-female": "vi-VN-HoaiMyNeural",
    "vi-male": "vi-VN-NamMinhNeural",
    "en-US-JennyNeural": "en-US-JennyNeural",
    "en-US-GuyNeural": "en-US-GuyNeural",
    "zh-CN-XiaoxiaoNeural": "zh-CN-XiaoxiaoNeural",
    "zh-CN-YunxiNeural": "zh-CN-YunxiNeural",
    "ja-JP-NanamiNeural": "ja-JP-NanamiNeural",
    "ja-JP-KeitaNeural": "ja-JP-KeitaNeural",
    "ko-KR-SunHiNeural": "ko-KR-SunHiNeural",
    "ko-KR-InJoonNeural": "ko-KR-InJoonNeural",
}

DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
MAX_CHUNK_CHARS = 500
LRU_MAX_SIZE = 100


@dataclass(frozen=True)
class ChunkResult:
    chunk_index: int
    audio_bytes: bytes


class _LruTtsCache:
    """Bounded LRU keyed by (text+voice+rate+pitch) sha256.

    Mirrors the cache strategy of xTTS micro-service: bounded size, simple
    FIFO eviction. Process-local; multi-instance deployments should swap
    for redis later.
    """

    def __init__(self, maxsize: int = LRU_MAX_SIZE) -> None:
        self._data: "OrderedDict[str, bytes]" = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> bytes | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: bytes) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self._maxsize:
            self._data.popitem(last=False)


def resolve_voice(voice_profile_id: str | None) -> str:
    if not voice_profile_id:
        return DEFAULT_VOICE
    if voice_profile_id in VOICE_MAP:
        return VOICE_MAP[voice_profile_id]
    if "-" in voice_profile_id and len(voice_profile_id) >= 6:
        return voice_profile_id
    return DEFAULT_VOICE


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split ``text`` into sentence-aligned chunks.

    The chunker respects sentence boundaries (``.``, ``!``, ``?``, newline) and
    never breaks inside a sentence if the sentence fits within ``max_chars``.
    Falls back to hard-split on whitespace if a single sentence is too long.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    sentences: list[str] = []
    buf: list[str] = []
    for ch in cleaned:
        buf.append(ch)
        if ch in ".!?\n":
            sentences.append("".join(buf).strip())
            buf = []
    if buf:
        sentences.append("".join(buf).strip())

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i : i + max_chars])
            continue
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = f"{current} {sentence}"
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def _cache_key(text: str, voice: str, rate: str, pitch: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"\x00")
    h.update(voice.encode("utf-8"))
    h.update(b"\x00")
    h.update(rate.encode("utf-8"))
    h.update(b"\x00")
    h.update(pitch.encode("utf-8"))
    return h.hexdigest()


class EdgeTtsProvider(Provider[TtsInput, TtsResponse]):
    """Free, GPU-less TTS via Microsoft Edge WebSocket service.

    Capabilities reflect that this provider is online (cloud) and does not
    require an API key — the only requirement is outbound HTTPS to
    ``*.api.cognitive.microsoft.com`` / ``*.edge.microsoft.com``.
    """

    id = "edge_tts"
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=False)

    def __init__(self, *, cache_size: int = LRU_MAX_SIZE) -> None:
        self._cache = _LruTtsCache(maxsize=cache_size)

    def fingerprint(self, payload: TtsInput) -> ArtifactSignature:
        cfg = payload.config or TtsProviderConfig()
        voice = resolve_voice(payload.voice_profile_id or cfg.voice_id)
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.text.encode("utf-8")).hexdigest()[:32],
            model_id=f"edge-{voice}",
            model_version="edge-tts",
            provider_build=self.id,
            config_hash=hashlib.sha256(
                f"{voice}|{cfg.speed}|{cfg.pitch}".encode("utf-8")
            ).hexdigest()[:16],
        )

    async def run(self, payload: TtsInput, *, ctx: ProviderContext) -> TtsResponse:
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")

        cfg = payload.config or TtsProviderConfig()
        voice = resolve_voice(payload.voice_profile_id or cfg.voice_id)
        rate = _format_rate(cfg.speed)
        pitch = _format_pitch(cfg.pitch)

        chunks = chunk_text(payload.text)
        if not chunks:
            raise CapabilityUnsupported("edge-tts-empty-text", "no content to synthesize")

        audio_bytes = b"".join(await asyncio.gather(*(self._synthesize_chunk(c, voice, rate, pitch) for c in chunks)))

        prefix = payload.output_storage_prefix or "tts"
        storage_key = f"{prefix}/{self.id}/{voice}/{os.urandom(8).hex()}.mp3"
        ctx.storage.upload(storage_key, audio_bytes, mime="audio/mpeg")
        duration_ms = _probe_duration_ms(audio_bytes)
        return TtsResponse(
            voice_profile_id=_to_uuid(payload.voice_profile_id),
            audio_storage_key=storage_key,
            duration_ms=duration_ms,
            sample_rate=24000,
            signature=self.fingerprint(payload),
            fallback_used=False,
        )

    async def _synthesize_chunk(self, text: str, voice: str, rate: str, pitch: str) -> bytes:
        key = _cache_key(text, voice, rate, pitch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        try:
            import edge_tts  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("edge-tts-not-installed", str(exc)) from exc

        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        buffer = io.BytesIO()
        try:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    buffer.write(chunk["data"])
        except Exception as exc:  # pragma: no cover - network error path
            raise CapabilityUnsupported("edge-tts-stream-failed", str(exc)) from exc
        data = buffer.getvalue()
        if not data:
            raise CapabilityUnsupported("edge-tts-empty-audio", f"no audio returned for voice={voice}")
        self._cache.put(key, data)
        return data


def _format_rate(speed: float) -> str:
    # Edge-TTS expects strings like "+0%" or "-25%"; clamp to FFmpeg-friendly range.
    pct = int(round((speed - 1.0) * 100))
    pct = max(-50, min(100, pct))
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


def _format_pitch(pitch_hz: float) -> str:
    # Edge-TTS expects "0Hz" or "-50Hz"; the project's TtsProviderConfig stores
    # pitch as a fractional Hz value, so we clamp to a sensible range.
    hz = int(round(pitch_hz))
    hz = max(-100, min(100, hz))
    sign = "+" if hz >= 0 else ""
    return f"{sign}{hz}Hz"


def _probe_duration_ms(mp3_bytes: bytes) -> int:
    """Rough duration probe.

    Edge-TTS streams MP3 at ~48 kbps mono. We avoid pulling in mutagen as a
    dependency just for this; the dubbing align pipeline re-probes with
    FFmpeg downstream for accuracy. This value is only used for the TTS
    response metadata.
    """
    if not mp3_bytes:
        return 1
    # ~6000 bytes per second at 48 kbps
    return max(1, len(mp3_bytes) * 1000 // 6000)


def list_voices() -> Iterable[str]:
    """Return the static VOICE_MAP keys for tests / docs."""
    return sorted(VOICE_MAP.keys())


def _to_uuid(value: object) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None
