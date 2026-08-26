"""Dubbing align provider via FFmpeg atempo chain."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from translator_api.providers.base import (
    CapabilityUnsupported,
    Provider,
    ProviderCapabilities,
    ProviderContext,
)
from translator_shared.providers import ArtifactSignature
from translator_shared.provider_configs import DubbingAlignProviderConfig
from translator_shared.provider_responses_extra import AudioMixResponse


@dataclass(frozen=True)
class DubbingAlignInput:
    voice_storage_key: str
    target_duration_ms: int
    source_duration_ms: int
    output_storage_prefix: str = "align"
    config: DubbingAlignProviderConfig | None = None


class FfmpegAtempoAlignProvider(Provider[DubbingAlignInput, AudioMixResponse]):
    id = "ffmpeg_atempo"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def fingerprint(self, payload: DubbingAlignInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.voice_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: DubbingAlignInput, *, ctx: ProviderContext) -> AudioMixResponse:
        cfg = payload.config or DubbingAlignProviderConfig()
        if shutil.which(cfg.ffmpeg_path) is None:
            raise CapabilityUnsupported("ffmpeg-missing", f"ffmpeg not on PATH at {cfg.ffmpeg_path}")
        if payload.source_duration_ms <= 0 or payload.target_duration_ms <= 0:
            raise CapabilityUnsupported("dubbing-align-invalid-duration", "source/target duration must be > 0")
        ratio = payload.source_duration_ms / payload.target_duration_ms
        ratio = max(cfg.min_speed, min(cfg.max_speed, ratio))
        audio_path = _materialize(payload.voice_storage_key, ctx)
        output_path = str(Path(tempfile.gettempdir()) / "translator-align" / f"{os.urandom(8).hex()}.wav")
        atempo_filters = _build_atempo_chain(ratio)
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            audio_path,
            "-filter:a",
            ",".join(atempo_filters),
            "-ar",
            "48000",
            output_path,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            raise CapabilityUnsupported("ffmpeg-align-failed", exc.stderr.decode("utf-8", errors="ignore")[:512]) from exc
        with open(output_path, "rb") as fh:
            data = fh.read()
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        output_key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.wav"
        ctx.storage.upload(output_key, data, mime="audio/wav")
        return AudioMixResponse(
            output_key=output_key,
            duration_ms=payload.target_duration_ms,
            sample_rate=48000,
            signature=self.fingerprint(payload),
        )


def _build_atempo_chain(ratio: float) -> list[str]:
    if abs(ratio - 1.0) < 1e-3:
        return ["atempo=1.0"]
    factors: list[float] = []
    remaining = ratio
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return [f"atempo={factor:.4f}" for factor in factors]


def _materialize(storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    tmp = Path(tempfile.gettempdir()) / "translator-align-input"
    tmp.mkdir(parents=True, exist_ok=True)
    target = tmp / Path(storage_key).name
    ctx.storage.download_to_path(storage_key, str(target))
    return str(target)