"""Voice cloning provider base."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pydantic import BaseModel
from translator_api.providers.base import Provider, ProviderCapabilities, ProviderContext
from translator_shared.providers import ArtifactSignature


@dataclass(frozen=True)
class VoiceEmbeddingInput:
    audio_storage_key: str
    speaker_id: str


class VoiceEmbeddingResponse(BaseModel):
    embedding_storage_key: str
    embedding_dim: int
    sample_rate: int
    model_id: str


@dataclass(frozen=True)
class VoiceCloneInput:
    text: str
    embedding_storage_key: str
    speaker_id: str
    target_language: str = "vi"
    output_storage_prefix: str = "voice_clone"


class VoiceCloneResponse(BaseModel):
    output_storage_key: str
    sample_rate: int
    duration_ms: int
    speaker_id: str
    signature: ArtifactSignature


class VoiceEmbeddingProvider(Provider[VoiceEmbeddingInput, VoiceEmbeddingResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: VoiceEmbeddingInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.audio_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: VoiceEmbeddingInput, *, ctx: ProviderContext) -> VoiceEmbeddingResponse:
        return self._compute_embedding(payload, ctx)

    def _compute_embedding(self, payload: VoiceEmbeddingInput, ctx: ProviderContext) -> VoiceEmbeddingResponse:  # pragma: no cover - abstract
        raise NotImplementedError


class VoiceCloneProvider(Provider[VoiceCloneInput, VoiceCloneResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: VoiceCloneInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(f"{payload.speaker_id}|{payload.text}".encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: VoiceCloneInput, *, ctx: ProviderContext) -> VoiceCloneResponse:
        raise NotImplementedError

    async def synthesize(self, payload: VoiceCloneInput, *, ctx: ProviderContext) -> VoiceCloneResponse:  # pragma: no cover - abstract
        raise NotImplementedError
