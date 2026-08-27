"""Qwen3-TTS engine adapter for the TTS microservice."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class Qwen3Request:
    text: str
    voice: str
    speed: float = 1.0
    pitch: float = 0.0
    sample_rate: int = 24000


class Qwen3TtsEngine:
    """Local Qwen3-TTS inference adapter.

    The engine lazy-loads the SDK so the microservice stays importable on
    machines without the model checkpoint installed. When the SDK or
    checkpoint is missing, calls raise ``RuntimeError`` and the
    ``/readyz`` endpoint reports the engine as not-ready.
    """

    VOICE_ALIASES: dict[str, str] = {
        "qwen-vi-female": "qwen-vi-female",
        "qwen-vi-male": "qwen-vi-male",
        "qwen-en-female": "qwen-en-female",
        "qwen-en-male": "qwen-en-male",
        "qwen-zh-female": "qwen-zh-female",
        "vi-female": "qwen-vi-female",
        "vi-male": "qwen-vi-male",
        "en-female": "qwen-en-female",
        "en-male": "qwen-en-male",
        "zh-female": "qwen-zh-female",
    }
    DEFAULT_VOICE = "qwen-vi-female"

    def __init__(self) -> None:
        self._loaded = False
        self._model = None
        self._load_lock = asyncio.Lock()

    def is_ready(self) -> bool:
        return self._loaded

    def resolve_voice(self, voice: str | None) -> str:
        if not voice:
            return self.DEFAULT_VOICE
        return self.VOICE_ALIASES.get(voice, voice)

    def warmup(self) -> None:
        try:
            from qwen_tts import Qwen3TTS  # type: ignore[import-not-found]
        except Exception:
            return
        try:
            self._model = Qwen3TTS(model_id="qwen3-tts")
            self._loaded = True
        except Exception:
            self._loaded = False

    async def synthesize(self, req: Qwen3Request) -> bytes:
        if not self._loaded:
            async with self._load_lock:
                if not self._loaded:
                    self.warmup()
            if not self._loaded:
                raise RuntimeError("qwen3-tts-checkpoint-missing")

        try:
            audio = self._model.synthesize(  # type: ignore[union-attr]
                text=req.text,
                voice=req.voice,
                speed=req.speed,
                pitch=req.pitch,
                sample_rate=req.sample_rate,
            )
        except Exception as exc:  # pragma: no cover - model dependent
            raise RuntimeError(f"qwen3-synthesis-failed: {exc}") from exc

        if hasattr(audio, "tobytes"):
            return audio.tobytes()
        if isinstance(audio, (bytes, bytearray)):
            return bytes(audio)
        raise RuntimeError(f"unsupported-audio-type: {type(audio).__name__}")