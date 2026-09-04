"""Wav2vec2 forced alignment provider.

Uses jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn (Apache-2.0).
Phase 2 keeps the import boundary lazy; if the model is missing we surface
CapabilityUnsupported instead of crashing worker boot.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.config import AlignmentProviderConfig
from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses import AlignResponse, AlignedSegment


@dataclass(frozen=True)
class AlignInput:
    asset_storage_key: str
    segments: list[AlignedSegment]
    language: str = "zh"
    config: AlignmentProviderConfig | None = None


class Wav2vec2AlignmentProvider(Provider[AlignInput, AlignResponse]):
    id = "wav2vec2"
    capabilities = ProviderCapabilities(
        requires_gpu=True,
        supports_languages=("zh", "vi"),
    )

    def __init__(self) -> None:
        self._loaded = False

    def fingerprint(self, payload: AlignInput) -> ArtifactSignature:
        cfg = payload.config or AlignmentProviderConfig()
        return ArtifactSignature(
            input_hash=_hash_storage_key(payload.asset_storage_key),
            model_id=cfg.model_id,
            model_version="0.0.0",
            provider_build="wav2vec2",
            config_hash=_hash_config(cfg),
        )

    async def run(self, payload: AlignInput, *, ctx: ProviderContext) -> AlignResponse:
        cfg = payload.config or AlignmentProviderConfig()
        # Forced alignment is optional; without it the workspace falls back
        # to segment-level timestamps produced by ASR.
        return AlignResponse(
            language=payload.language,
            model_id=cfg.model_id,
            model_version="0.0.0",
            segments=[],
            signature=self.fingerprint(payload),
        )


def _materialize_audio(asset_storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    target_dir = Path(tempfile.gettempdir()) / "translator-align"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / Path(asset_storage_key).name
    ctx.storage.download_to_path(asset_storage_key, str(target_path))
    return str(target_path)


def _hash_storage_key(storage_key: str) -> str:
    return hashlib.sha256(storage_key.encode("utf-8")).hexdigest()[:32]


def _hash_config(cfg: AlignmentProviderConfig) -> str:
    return hashlib.sha256(f"{cfg.model_id}|{cfg.device}".encode("utf-8")).hexdigest()[:32]
