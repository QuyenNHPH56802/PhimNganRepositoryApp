"""Audio separation providers."""

import hashlib

from translator_api.providers.base import ProviderCapabilities, ProviderContext
from translator_api.providers.separation.base import (
    LocalSeparationProvider,
    SeparationInput,
    upload_separation_output,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses_extra import SeparationResponse


class Uvr5MdxProvider(LocalSeparationProvider):
    id = "uvr5_mdx"
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: SeparationInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.asset_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=payload.config.model_id if payload.config else "MDX23K",
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def _run_separation(self, payload: SeparationInput, ctx: ProviderContext) -> SeparationResponse:
        self._ensure_model(payload.config)
        audio_path = self._materialize_audio(payload.asset_storage_key, ctx)
        _ = audio_path
        return SeparationResponse(
            vocals_key=upload_separation_output(ctx, payload.asset_storage_key, "vocals", self.id),
            background_key=upload_separation_output(ctx, payload.asset_storage_key, "instrumental", self.id),
            method=self.id,
            duration_ms=0,
            signature=self.fingerprint(payload),
        )


class DemucsProvider(LocalSeparationProvider):
    id = "demucs"
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: SeparationInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.asset_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=payload.config.model_id if payload.config else "htdemucs",
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def _run_separation(self, payload: SeparationInput, ctx: ProviderContext) -> SeparationResponse:
        self._ensure_model(payload.config)
        return SeparationResponse(
            vocals_key=upload_separation_output(ctx, payload.asset_storage_key, "vocals", self.id),
            background_key=upload_separation_output(ctx, payload.asset_storage_key, "no_vocals", self.id),
            method=self.id,
            duration_ms=0,
            signature=self.fingerprint(payload),
        )


class BsRoformerProvider(LocalSeparationProvider):
    id = "bs_roformer"
    capabilities = ProviderCapabilities(requires_gpu=True)

    def fingerprint(self, payload: SeparationInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.asset_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=payload.config.model_id if payload.config else "BS-Roformer",
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def _run_separation(self, payload: SeparationInput, ctx: ProviderContext) -> SeparationResponse:
        self._ensure_model(payload.config)
        return SeparationResponse(
            vocals_key=upload_separation_output(ctx, payload.asset_storage_key, "vocals", self.id),
            background_key=upload_separation_output(ctx, payload.asset_storage_key, "instrumental", self.id),
            method=self.id,
            duration_ms=0,
            signature=self.fingerprint(payload),
        )
