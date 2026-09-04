"""TTS provider base."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.providers.base import (
    CapabilityUnsupported,
    ConsentMissing,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.provider_configs import TtsProviderConfig
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses_extra import TtsResponse


@dataclass(frozen=True)
class TtsInput:
    text: str
    voice_profile_id: str | None = None
    reference_audio_key: str | None = None
    output_storage_prefix: str | None = None
    config: TtsProviderConfig | None = None


@dataclass(frozen=True)
class TtsOutputTarget:
    storage_key: str
    mime: str = "audio/wav"


class LocalTtsProvider(Provider[TtsInput, TtsResponse]):
    """Common base for on-prem TTS providers (VietVoice/VieNeu/CosyVoice/MeloTTS)."""

    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def __init__(self) -> None:
        self._loaded = False

    def fingerprint(self, payload: TtsInput) -> ArtifactSignature:
        cfg = payload.config or TtsProviderConfig()
        return ArtifactSignature(
            input_hash=str(abs(hash(payload.text)) % (2**32)),
            model_id=cfg.model_id,
            model_version=cfg.model_id,
            provider_build=self.id,
            config_hash=str(abs(hash(repr(cfg))) % (2**32)),
        )

    async def run(self, payload: TtsInput, *, ctx: ProviderContext) -> TtsResponse:
        if not self._ensure_consent(payload):
            raise ConsentMissing(f"{self.id}-consent-missing", "voice profile lacks grant")
        try:
            self._ensure_loaded(payload.config)
        except CapabilityUnsupported:
            raise
        except Exception as exc:
            raise CapabilityUnsupported(f"{self.id}-load-failed", str(exc)) from exc

        audio_bytes = self._synthesize(payload)
        storage_key = self._upload(payload, ctx, audio_bytes)
        duration_ms = self._probe_duration_ms(audio_bytes)
        return TtsResponse(
            voice_profile_id=None,
            audio_storage_key=storage_key,
            duration_ms=duration_ms,
            sample_rate=payload.config.sample_rate if payload.config else 24000,
            signature=self.fingerprint(payload),
            fallback_used=False,
        )

    def _ensure_consent(self, payload: TtsInput) -> bool:
        return True

    def _ensure_loaded(self, config: TtsProviderConfig | None) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def _synthesize(self, payload: TtsInput) -> bytes:  # pragma: no cover - abstract
        raise NotImplementedError

    def _upload(self, payload: TtsInput, ctx: ProviderContext, data: bytes) -> str:
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        prefix = payload.output_storage_prefix or "tts"
        key = f"{prefix}/{self.id}/{payload.voice_profile_id or 'default'}/{os.urandom(8).hex()}.wav"
        ctx.storage.upload(key, data, mime="audio/wav")
        return key

    def _probe_duration_ms(self, data: bytes) -> int:
        return max(1, len(data) // 48)


class CloudTtsProvider(Provider[TtsInput, TtsResponse]):
    """Common base for cloud HTTP TTS providers (Azure / Google / ElevenLabs)."""

    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=False, is_local=False)

    def __init__(self, *, base_url: str, api_key_env: str) -> None:
        self._base_url = base_url
        self._api_key_env = api_key_env

    def fingerprint(self, payload: TtsInput) -> ArtifactSignature:
        cfg = payload.config or TtsProviderConfig()
        return ArtifactSignature(
            input_hash=str(abs(hash(payload.text)) % (2**32)),
            model_id=cfg.model_id,
            model_version=cfg.model_id,
            provider_build=self.id,
            config_hash=str(abs(hash(repr(cfg))) % (2**32)),
        )

    async def run(self, payload: TtsInput, *, ctx: ProviderContext) -> TtsResponse:
        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise CapabilityUnsupported(f"{self.id}-missing-api-key", f"env {self._api_key_env} not set")
        try:
            import httpx  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("translate-httpx-missing", str(exc)) from exc
        audio_bytes = await self._call_http(payload, api_key, httpx)
        storage_key = self._upload(payload, ctx, audio_bytes)
        return TtsResponse(
            voice_profile_id=None,
            audio_storage_key=storage_key,
            duration_ms=max(1, len(audio_bytes) // 48),
            sample_rate=payload.config.sample_rate if payload.config else 24000,
            signature=self.fingerprint(payload),
            fallback_used=False,
        )

    async def _call_http(self, payload: TtsInput, api_key: str, httpx) -> bytes:  # pragma: no cover - abstract
        raise NotImplementedError

    def _upload(self, payload: TtsInput, ctx: ProviderContext, data: bytes) -> str:
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        prefix = payload.output_storage_prefix or "tts"
        key = f"{prefix}/{self.id}/{payload.voice_profile_id or 'default'}/{os.urandom(8).hex()}.wav"
        ctx.storage.upload(key, data, mime="audio/wav")
        return key


def temp_wav_path(suffix: str = ".wav") -> str:
    tmp = Path(tempfile.gettempdir()) / "translator-tts"
    tmp.mkdir(parents=True, exist_ok=True)
    return str(tmp / f"{os.urandom(8).hex()}{suffix}")
