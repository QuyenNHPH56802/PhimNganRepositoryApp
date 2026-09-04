"""FFmpeg-based render provider."""

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
from translator_shared.provider_configs import RenderProviderConfig
from translator_shared.provider_responses_extra import RenderResponse


@dataclass(frozen=True)
class RenderInput:
    source_video_key: str
    dubbed_audio_key: str | None
    subtitle_ass_key: str | None = None
    output_storage_prefix: str = "render"
    config: RenderProviderConfig | None = None


class FfmpegRenderProvider(Provider[RenderInput, RenderResponse]):
    id = "ffmpeg_render"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def fingerprint(self, payload: RenderInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.source_video_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash=hashlib.sha256(repr(payload.config).encode("utf-8")).hexdigest()[:32] if payload.config else "pending",
        )

    async def run(self, payload: RenderInput, *, ctx: ProviderContext) -> RenderResponse:
        cfg = payload.config or RenderProviderConfig()
        if shutil.which(cfg.ffmpeg_path) is None:
            raise CapabilityUnsupported("ffmpeg-missing", f"ffmpeg not on PATH at {cfg.ffmpeg_path}")
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")

        video_path = _materialize(payload.source_video_key, ctx)
        audio_path = _materialize(payload.dubbed_audio_key, ctx) if payload.dubbed_audio_key else None
        subtitle_path = _materialize(payload.subtitle_ass_key, ctx) if payload.subtitle_ass_key else None

        render_dir = Path(tempfile.gettempdir()) / "translator-render"
        render_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(render_dir / f"{os.urandom(8).hex()}.mp4")
        cmd = [cfg.ffmpeg_path, "-y", "-i", video_path]
        if audio_path:
            cmd += ["-i", audio_path]
        if subtitle_path:
            cmd += ["-i", subtitle_path]
        cmd += ["-map", "0:v", "-c:v", "libx264", "-crf", str(cfg.crf), "-preset", cfg.preset]
        if audio_path:
            cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
        if subtitle_path:
            cmd += ["-map", "2:s?", "-c:s", "mov_text"]
        cmd += ["-shortest", output_path]
        if cfg.hwaccel:
            cmd.insert(1, "-hwaccel")
            cmd.insert(2, cfg.hwaccel)
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            raise CapabilityUnsupported("ffmpeg-render-failed", exc.stderr.decode("utf-8", errors="ignore")[:512]) from exc

        with open(output_path, "rb") as fh:
            data = fh.read()
        output_key = f"{payload.output_storage_prefix}/{self.id}/{os.urandom(8).hex()}.mp4"
        ctx.storage.upload(output_key, data, mime="video/mp4")
        return RenderResponse(
            output_key=output_key,
            duration_ms=max(1, len(data) // 1024),
            validation={"size_bytes": len(data)},
            signature=self.fingerprint(payload),
        )


def _materialize(storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    tmp = Path(tempfile.gettempdir()) / "translator-render-input"
    tmp.mkdir(parents=True, exist_ok=True)
    target = tmp / Path(storage_key).name
    ctx.storage.download_to_path(storage_key, str(target))
    return str(target)
