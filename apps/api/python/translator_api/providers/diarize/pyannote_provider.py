"""Pyannote speaker diarization provider.

Uses pyannote/speaker-diarization-3.1 (CC-BY-4.0, gated). HF token required;
missing token raises ConsentMissing so the worker surfaces a clear error
without re-attempting forever.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.config import DiarizationProviderConfig
from translator_api.providers.base import (
    CapabilityUnsupported,
    ConsentMissing,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_responses import DiarizeResponse, SpeakerTurn


@dataclass(frozen=True)
class DiarizeInput:
    asset_storage_key: str
    config: DiarizationProviderConfig | None = None


class PyannoteDiarizationProvider(Provider[DiarizeInput, DiarizeResponse]):
    id = "pyannote_3_1"
    capabilities = ProviderCapabilities(
        requires_gpu=True,
        requires_consent=True,
    )

    def __init__(self) -> None:
        self._loaded = False

    def fingerprint(self, payload: DiarizeInput) -> ArtifactSignature:
        cfg = payload.config or DiarizationProviderConfig()
        return ArtifactSignature(
            input_hash=_hash_storage_key(payload.asset_storage_key),
            model_id=cfg.model_id,
            model_version="0.0.0",
            provider_build="pyannote",
            config_hash=_hash_config(cfg),
        )

    async def run(self, payload: DiarizeInput, *, ctx: ProviderContext) -> DiarizeResponse:
        cfg = payload.config or DiarizationProviderConfig()
        if not cfg.hf_token:
            raise ConsentMissing("pyannote-hf-token-required", "HF token is required for pyannote models")

        audio_path = _materialize_audio(payload.asset_storage_key, ctx)

        try:
            from pyannote.audio import Pipeline  # type: ignore[import-not-found]
        except Exception as exc:
            raise CapabilityUnsupported("pyannote-not-installed", str(exc)) from exc

        try:
            pipeline = Pipeline.from_pretrained(cfg.model_id, use_auth_token=cfg.hf_token)
            if cfg.min_speakers is not None or cfg.max_speakers is not None:
                pipeline.instantiate({"cluster": {"min_cluster_size": cfg.min_speakers or 1, "max_cluster_size": cfg.max_speakers or 20}})
        except Exception as exc:
            msg = str(exc).lower()
            if "gated" in msg or "auth" in msg or "401" in msg:
                raise ConsentMissing("pyannote-hf-auth-failed", str(exc)) from exc
            raise CapabilityUnsupported("pyannote-model-unavailable", str(exc)) from exc

        try:
            diarization = pipeline(audio_path)
        except Exception as exc:
            raise CapabilityUnsupported("pyannote-runtime", str(exc)) from exc

        turns: list[SpeakerTurn] = []
        speakers: set[str] = set()
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            turns.append(
                SpeakerTurn(
                    speaker_label=speaker,
                    start_ms=int(turn.start * 1000),
                    end_ms=int(turn.end * 1000),
                )
            )

        return DiarizeResponse(
            model_id=cfg.model_id,
            model_version="3.1",
            num_speakers=len(speakers),
            turns=turns,
            signature=self.fingerprint(payload),
        )


def _materialize_audio(asset_storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    target_dir = Path(tempfile.gettempdir()) / "translator-diarize"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / Path(asset_storage_key).name
    ctx.storage.download_to_path(asset_storage_key, str(target_path))
    return str(target_path)


def _hash_storage_key(storage_key: str) -> str:
    return hashlib.sha256(storage_key.encode("utf-8")).hexdigest()[:32]


def _hash_config(cfg: DiarizationProviderConfig) -> str:
    payload = f"{cfg.model_id}|{cfg.device}|min={cfg.min_speakers}|max={cfg.max_speakers}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]