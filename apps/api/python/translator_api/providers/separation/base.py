"""Separation provider base."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.provider_configs import SeparationProviderConfig
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses_extra import SeparationResponse


@dataclass(frozen=True)
class SeparationInput:
    asset_storage_key: str
    output_prefix: str = "separation"
    config: SeparationProviderConfig | None = None


class LocalSeparationProvider(Provider[SeparationInput, SeparationResponse]):
    id: str = ""
    capabilities = ProviderCapabilities(requires_gpu=True)

    def __init__(self) -> None:
        self._loaded = False

    def fingerprint(self, payload: SeparationInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash="pending",
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: SeparationInput, *, ctx: ProviderContext) -> SeparationResponse:
        self._ensure_model(payload.config)
        return await self._run_separation(payload, ctx)

    async def _run_separation(self, payload: SeparationInput, ctx: ProviderContext) -> SeparationResponse:  # pragma: no cover - abstract
        raise NotImplementedError

    def _ensure_model(self, config: SeparationProviderConfig | None) -> None:
        try:
            import torch  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported(f"{self.id}-torch-missing", str(exc)) from exc
        self._loaded = True

    def _materialize_audio(self, asset_storage_key: str, ctx: ProviderContext) -> str:
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        tmp_dir = Path(tempfile.gettempdir()) / f"translator-{self.id}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        target = tmp_dir / Path(asset_storage_key).name
        ctx.storage.download_to_path(asset_storage_key, str(target))
        return str(target)


def upload_separation_output(ctx: ProviderContext, asset_storage_key: str, kind: str, provider_id: str) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    key = f"separation/{provider_id}/{Path(asset_storage_key).stem}/{kind}/{os.urandom(8).hex()}.wav"
    ctx.storage.upload(key, b"", mime="audio/wav")
    return key
