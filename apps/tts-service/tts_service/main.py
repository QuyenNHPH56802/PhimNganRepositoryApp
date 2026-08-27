"""FastAPI entrypoint for the TTS microservice.

Patterned after xdev-asia-labs/xTTS: a thin service that exposes
``/synthesize`` over HTTP, holds an LRU cache keyed by
``sha256(text+voice+rate+pitch)``, and dispatches to either the Edge-TTS
or Qwen3-TTS engine depending on the request.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tts_service.cache import TtsLruCache
from tts_service.chunker import chunk_text
from tts_service.engines.edge import EdgeTtsEngine
from tts_service.engines.qwen3 import Qwen3Request, Qwen3TtsEngine

PORT = int(os.environ.get("PORT", "3099"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")
TTS_MAX_CHUNK = int(os.environ.get("TTS_MAX_CHUNK", "500"))
TTS_MAX_RETRIES = int(os.environ.get("TTS_MAX_RETRIES", "3"))
TTS_MAX_TEXT_LENGTH = int(os.environ.get("TTS_MAX_TEXT_LENGTH", "20000"))
TTS_DEFAULT_VOICE = os.environ.get("TTS_DEFAULT_VOICE", "vi-VN-HoaiMyNeural")
TTS_CONCURRENCY = int(os.environ.get("TTS_CONCURRENCY", "2"))
TTS_CACHE_SIZE = int(os.environ.get("TTS_CACHE_SIZE", "100"))

_engine_kind = os.environ.get("TTS_ENGINE", "edge").lower()
_edge = EdgeTtsEngine()
_qwen3 = Qwen3TtsEngine()
_cache = TtsLruCache(maxsize=TTS_CACHE_SIZE)
_semaphore = asyncio.Semaphore(TTS_CONCURRENCY)
_start_ts = time.time()


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=TTS_MAX_TEXT_LENGTH)
    voice: str | None = None
    rate: float = 1.0
    pitch: float = 0.0
    engine: Literal["edge", "qwen3"] | None = None
    sample_rate: int = 24000


class SynthesizeResponse(BaseModel):
    audio_b64: str
    mime: str
    duration_ms: int
    voice: str
    engine: str
    cache_hit: bool
    chunk_count: int


def create_app() -> FastAPI:
    app = FastAPI(
        title="Translator TTS Service",
        version="0.1.0",
        description="Standalone TTS microservice (Edge-TTS + Qwen3-TTS).",
    )

    @app.on_event("startup")
    async def _startup() -> None:
        if _engine_kind == "qwen3":

            async def _bg_warmup() -> None:
                await asyncio.to_thread(_qwen3.warmup)

            asyncio.create_task(_bg_warmup())

    @app.get("/healthz")
    async def healthz() -> dict[str, object]:
        return {"status": "ok", "uptime_s": int(time.time() - _start_ts)}

    @app.get("/readyz")
    async def readyz() -> dict[str, object]:
        return {
            "status": "ok",
            "engine": _engine_kind,
            "qwen3_ready": _qwen3.is_ready(),
            "cache": _cache.stats(),
        }

    @app.get("/voices")
    async def voices(lang: str | None = None) -> dict[str, object]:
        items = [
            {"name": v, "gender": _gender(v), "locale": v.split("-", 1)[0] if "-" in v else lang}
            for v in sorted(EdgeTtsEngine.VOICE_ALIASES.keys())
            if not lang or v.lower().startswith(lang.lower())
        ]
        return {"voices": items, "total": len(items), "engine": _engine_kind}

    @app.post("/synthesize", response_model=SynthesizeResponse)
    async def synthesize(req: SynthesizeRequest) -> SynthesizeResponse:
        if len(req.text) > TTS_MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"text exceeds TTS_MAX_TEXT_LENGTH={TTS_MAX_TEXT_LENGTH}",
            )

        engine = (req.engine or _engine_kind or "edge").lower()
        chunks = chunk_text(req.text, max_chars=TTS_MAX_CHUNK)
        if not chunks:
            raise HTTPException(status_code=400, detail="empty text after chunking")

        if engine == "qwen3":
            voice = _qwen3.resolve_voice(req.voice or Qwen3TtsEngine.DEFAULT_VOICE)
            rate = EdgeTtsEngine.format_rate(req.rate)
            pitch = EdgeTtsEngine.format_pitch(req.pitch)
            audio, cache_hit = await _synthesize_qwen3(
                chunks, voice, rate, pitch, req.sample_rate
            )
            mime = "audio/wav"
        else:
            voice = _edge.resolve_voice(req.voice or TTS_DEFAULT_VOICE)
            rate = EdgeTtsEngine.format_rate(req.rate)
            pitch = EdgeTtsEngine.format_pitch(req.pitch)
            audio, cache_hit = await _synthesize_edge(chunks, voice, rate, pitch)
            mime = "audio/mpeg"

        import base64

        return SynthesizeResponse(
            audio_b64=base64.b64encode(audio).decode("ascii"),
            mime=mime,
            duration_ms=max(1, len(audio) * 1000 // 6000),
            voice=voice,
            engine=engine,
            cache_hit=cache_hit,
            chunk_count=len(chunks),
        )

    return app


async def _synthesize_edge(chunks: list[str], voice: str, rate: str, pitch: str) -> tuple[bytes, bool]:
    results: list[bytes] = []
    any_hit = False

    async def _one(idx: int, text: str) -> bytes:
        nonlocal any_hit
        async with _semaphore:
            cached = _cache.get(text, voice, rate, pitch)
            if cached is not None:
                any_hit = True
                return cached
            last_err: Exception | None = None
            for attempt in range(TTS_MAX_RETRIES):
                try:
                    audio = await _edge.synthesize_chunk(text, voice, rate, pitch)
                    _cache.put(text, voice, rate, pitch, audio)
                    return audio
                except Exception as exc:
                    last_err = exc
                    await asyncio.sleep(min(2**attempt, 4))
            raise HTTPException(status_code=502, detail=f"edge-tts-failed: {last_err}")

    results = await asyncio.gather(*(_one(i, c) for i, c in enumerate(chunks)))
    return b"".join(results), any_hit


async def _synthesize_qwen3(
    chunks: list[str], voice: str, rate: str, pitch: str, sample_rate: int
) -> tuple[bytes, bool]:
    results: list[bytes] = []
    any_hit = False

    async def _one(idx: int, text: str) -> bytes:
        nonlocal any_hit
        async with _semaphore:
            cached = _cache.get(text, voice, rate, pitch)
            if cached is not None:
                any_hit = True
                return cached
            last_err: Exception | None = None
            for attempt in range(TTS_MAX_RETRIES):
                try:
                    audio = await _qwen3.synthesize(
                        Qwen3Request(
                            text=text,
                            voice=voice,
                            speed=float(rate.replace("%", "").replace("+", "")) / 100 + 1.0,
                            pitch=float(pitch.replace("Hz", "").replace("+", "")),
                            sample_rate=sample_rate,
                        )
                    )
                    _cache.put(text, voice, rate, pitch, audio)
                    return audio
                except Exception as exc:
                    last_err = exc
                    await asyncio.sleep(min(2**attempt, 4))
            raise HTTPException(status_code=502, detail=f"qwen3-synthesis-failed: {last_err}")

    results = await asyncio.gather(*(_one(i, c) for i, c in enumerate(chunks)))
    return b"".join(results), any_hit


def _gender(voice: str) -> str:
    name = voice.lower()
    if "male" in name and "female" not in name:
        return "Male"
    if "female" in name:
        return "Female"
    return "Unknown"


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("tts_service.main:app", host="0.0.0.0", port=PORT, log_level=LOG_LEVEL)
