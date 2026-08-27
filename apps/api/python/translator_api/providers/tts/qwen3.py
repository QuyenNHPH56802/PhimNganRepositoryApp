"""Qwen3-TTS provider (Alibaba, multilingual, high quality).

Qwen3-TTS is Alibaba's local TTS model with broad multilingual coverage
(Chinese, English, Vietnamese, Japanese, Korean and 10+ languages). It is
deployed on-prem via the `qwen-tts` Python SDK and a model checkpoint
hosted on HuggingFace.

Following the same lazy-load pattern as CosyVoice3Provider and VieNeu, the
SDK is imported inside ``_ensure_loaded``. When the SDK is missing, calls
raise ``CapabilityUnsupported("qwen3-not-installed")`` so the activity
fallback chain can pivot to another provider.
"""

from __future__ import annotations

import hashlib
import os

from translator_api.providers.base import (
    CapabilityUnsupported,
    ProviderContext,
)
from translator_api.providers.tts.base import LocalTtsProvider, TtsInput
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_configs import TtsProviderConfig
from translator_shared.provider_responses_extra import TtsResponse


class Qwen3TtsProvider(LocalTtsProvider):
    id = "qwen3_tts"

    def __init__(self) -> None:
        super().__init__()
        self._loaded_voice: str | None = None

    def fingerprint(self, payload: TtsInput) -> ArtifactSignature:
        cfg = payload.config or TtsProviderConfig()
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.text.encode("utf-8")).hexdigest()[:32],
            model_id=f"qwen3-tts-{cfg.voice_id}",
            model_version=cfg.model_id,
            provider_build=self.id,
            config_hash=hashlib.sha256(
                f"{cfg.voice_id}|{cfg.speed}|{cfg.pitch}".encode("utf-8")
            ).hexdigest()[:16],
        )

    def _ensure_loaded(self, config: TtsProviderConfig | None) -> None:
        try:
            import qwen_tts  # type: ignore[import-not-found]  # noqa: F401
        except Exception as exc:
            raise CapabilityUnsupported("qwen3-not-installed", str(exc)) from exc
        cfg = config or TtsProviderConfig()
        if cfg.voice_id and cfg.voice_id != self._loaded_voice:
            self._loaded_voice = cfg.voice_id
        self._loaded = True

    def _synthesize(self, payload: TtsInput) -> bytes:
        if not self._loaded:
            raise CapabilityUnsupported("qwen3-not-loaded", "Qwen3-TTS SDK was not loaded")
        # Real SDK call is wrapped in a capability-missing fallback so the
        # provider surface remains usable in environments without the
        # checkpoint installed. The activity fallback chain will pick a
        # different provider in that case.
        cfg = payload.config or TtsProviderConfig()
        return _synthesize_with_qwen3(payload.text, cfg)

    async def run(self, payload: TtsInput, *, ctx: ProviderContext) -> TtsResponse:
        # Defer to the standard LocalTtsProvider contract for upload/storage
        # and signature, then enrich with provider-specific response metadata.
        import time as _time

        from translator_api.observability.metrics import observe_tts_call

        started = _time.perf_counter()
        try:
            result = await super().run(payload, ctx=ctx)
        except Exception:
            observe_tts_call(provider=self.id, generate_seconds=_time.perf_counter() - started)
            raise
        elapsed = _time.perf_counter() - started
        audio_seconds = result.duration_ms / 1000.0 if getattr(result, "duration_ms", 0) else None
        observe_tts_call(
            provider=self.id,
            generate_seconds=elapsed,
            audio_seconds=audio_seconds,
        )
        return TtsResponse(
            voice_profile_id=result.voice_profile_id or payload.voice_profile_id,
            audio_storage_key=result.audio_storage_key,
            duration_ms=result.duration_ms,
            sample_rate=result.sample_rate,
            signature=result.signature or self.fingerprint(payload),
            fallback_used=result.fallback_used,
        )


def _synthesize_with_qwen3(text: str, cfg: TtsProviderConfig) -> bytes:
    """Invoke the Qwen3-TTS SDK.

    Importing the SDK lazily keeps the API process importable in environments
    that don't host the model. When the SDK is present but a checkpoint
    download has not been completed, we raise ``CapabilityUnsupported`` so
    callers fall back instead of crashing.
    """
    try:
        from qwen_tts import Qwen3TTS  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - import branch
        raise CapabilityUnsupported("qwen3-not-installed", str(exc)) from exc

    try:
        model = Qwen3TTS(model_id=cfg.model_id or "qwen3-tts")
        audio = model.synthesize(
            text=text,
            voice=cfg.voice_id,
            speed=cfg.speed,
            pitch=cfg.pitch,
            sample_rate=cfg.sample_rate,
        )
    except Exception as exc:
        raise CapabilityUnsupported("qwen3-synthesis-failed", str(exc)) from exc

    if hasattr(audio, "tobytes"):
        return audio.tobytes()
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio)
    raise CapabilityUnsupported("qwen3-unsupported-audio", f"unexpected audio type: {type(audio)}")


def _ensure_storage_dir(prefix: str, voice: str) -> str:
    return f"{prefix}/qwen3_tts/{voice}/{os.urandom(8).hex()}.wav"
