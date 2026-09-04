"""Voice cloning provider base.

A voice cloning provider takes a sample audio and produces:
- An "embedding" (a vector representing the speaker's voice)
- Optionally a "preview" TTS sample to validate the clone

The current `VoiceCloneResponse` exposes:
- `embedding_storage_key`: pointer to the saved embedding blob (bytes/array)
- `preview_storage_key`: pointer to a short synthetic TTS preview
- `duration_ms`: how long the source sample was
- `quality_score`: provider's self-rated score (0..1)

Real implementations (XTTS, OpenVoice, CosyVoice) belong in `xtts_provider.py`
etc. and raise `CapabilityUnsupported` until model weights are available.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_shared.providers import ArtifactSignature


@dataclass(frozen=True)
class VoiceCloneInput:
    sample_storage_key: str
    provider_id: str = "voice.mock"
    strategy: Literal["full", "embedding_only"] = "embedding_only"
    text_preview: str | None = None


class VoiceCloneResponse(BaseModel):
    embedding_storage_key: str
    preview_storage_key: str | None = None
    duration_ms: int
    quality_score: float
    provider_id: str
    method: str
    signature: ArtifactSignature


class VoiceCloneProvider(Provider[VoiceCloneInput, VoiceCloneResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: VoiceCloneInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.sample_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: VoiceCloneInput, *, ctx: ProviderContext) -> VoiceCloneResponse:
        return await self._run_cloning(payload, ctx)

    async def _run_cloning(
        self, payload: VoiceCloneInput, ctx: ProviderContext
    ) -> VoiceCloneResponse:  # pragma: no cover - abstract
        raise NotImplementedError


def upload_voice_clone_embedding(
    ctx: ProviderContext, sample_storage_key: str, provider_id: str
) -> str:
    """Return a deterministic storage key for the embedding blob."""
    if ctx.storage is None:
        from translator_api.providers.base import CapabilityUnsupported
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    key = f"voice_clone/{provider_id}/{hashlib.sha1(sample_storage_key.encode()).hexdigest()[:12]}/embedding.bin"
    ctx.storage.upload(key, b"\x00\x00\x00\x00", mime="application/octet-stream")
    return key
