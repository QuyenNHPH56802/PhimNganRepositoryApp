"""Audio mix provider via FFmpeg."""

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
from translator_shared.provider_configs import MixProviderConfig
from translator_shared.provider_responses_extra import AudioMixResponse


@dataclass(frozen=True)
class MixInput:
    voice_storage_key: str
    background_storage_key: str | None = None
    output_storage_prefix: str = "mix"
    config: MixProviderConfig | None = None


class FfmpegMixProvider(Provider[MixInput, AudioMixResponse]):
    id = "ffmpeg_mix"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self._ffmpeg = ffmpeg_path or "ffmpeg"

    def fingerprint(self, payload: MixInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256((payload.voice_storage_key + "|" + (payload.background_storage_key or "")).encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(payload.config).encode("utf-8")).hexdigest()[:32] if payload.config else "pending",
        )

    async def run(self, payload: MixInput, *, ctx: ProviderContext) -> AudioMixResponse:
        cfg = payload.config or MixProviderConfig()
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        if shutil.which(self._ffmpeg or cfg.ffmpeg_path) is None:
            raise CapabilityUnsupported("ffmpeg-missing", f"ffmpeg not on PATH at {cfg.ffmpeg_path}")

        voice_path = _materialize(payload.voice_storage_key, ctx)
        bg_path = _materialize(payload.background_storage_key, ctx) if payload.background_storage_key else None
        output_path = str(Path(tempfile.gettempdir()) / "translator-mix" / f"{os.urandom(8).hex()}.wav")

        cmd = [cfg.ffmpeg_path, "-y", "-i", voice_path]
        if bg_path:
            cmd += ["-i", bg_path]
        cmd += ["-filter_complex", _build_filtergraph(cfg, has_bg=bool(bg_path)), "-ar", "48000", output_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            raise CapabilityUnsupported("ffmpeg-mix-failed", exc.stderr.decode("utf-8", errors="ignore")[:512]) from exc

        with open(output_path, "rb") as fh:
            data = fh.read()
        output_key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.wav"
        ctx.storage.upload(output_key, data, mime="audio/wav")
        return AudioMixResponse(
            output_key=output_key,
            duration_ms=max(1, len(data) // 96),
            sample_rate=48000,
            signature=self.fingerprint(payload),
        )


def _build_filtergraph(cfg: MixProviderConfig, *, has_bg: bool) -> str:
    if not has_bg:
        return f"[0:a]volume={_db_to_linear(cfg.voice_volume_db)}[out]"
    if cfg.ducking:
        return (
            f"[1:a]volume={_db_to_linear(cfg.background_volume_db)}[bg];"
            f"[0:a]volume={_db_to_linear(cfg.voice_volume_db)}[v];"
            "[v][bg]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=500[mix];"
            "[mix]aresample=48000[out]"
        )
    return (
        f"[0:a]volume={_db_to_linear(cfg.voice_volume_db)}[v];"
        f"[1:a]volume={_db_to_linear(cfg.background_volume_db)}[bg];"
        "[v][bg]amix=inputs=2:normalize=0[mix];"
        "[mix]aresample=48000[out]"
    )


def _db_to_linear(db: float) -> float:
    return float(10 ** (db / 20))


def _materialize(storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    tmp = Path(tempfile.gettempdir()) / "translator-mix-input"
    tmp.mkdir(parents=True, exist_ok=True)
    target = tmp / Path(storage_key).name
    ctx.storage.download_to_path(storage_key, str(target))
    return str(target)
