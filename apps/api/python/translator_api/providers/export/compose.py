"""Multi-format export provider (mp4/mkv/webm)."""

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
from translator_shared.provider_configs import ExportProviderConfig, RenderProviderConfig
from translator_shared.provider_responses_extra import ExportResponse

FORMAT_CODECS = {
    "mp4": {"vcodec": "libx264", "acodec": "aac", "container": "mp4"},
    "mkv": {"vcodec": "libx264", "acodec": "aac", "container": "matroska"},
    "webm": {"vcodec": "libvpx-vp9", "acodec": "libopus", "container": "webm"},
}


@dataclass(frozen=True)
class ExportInput:
    render_storage_key: str
    formats: tuple[str, ...] = ("mp4",)
    render_config: RenderProviderConfig | None = None
    export_config: ExportProviderConfig | None = None


class FfmpegExportProvider(Provider[ExportInput, list[ExportResponse]]):
    id = "ffmpeg_export"
    capabilities = ProviderCapabilities(requires_gpu=False)

    def fingerprint(self, payload: ExportInput) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash=hashlib.sha256(payload.render_storage_key.encode("utf-8")).hexdigest()[:32],
            model_id=self.id,
            model_version="0.0.0",
            provider_build=self.id,
            config_hash="pending",
        )

    async def run(self, payload: ExportInput, *, ctx: ProviderContext) -> list[ExportResponse]:
        cfg = payload.export_config or ExportProviderConfig()
        render_cfg = payload.render_config or RenderProviderConfig()
        if shutil.which(render_cfg.ffmpeg_path) is None:
            raise CapabilityUnsupported("ffmpeg-missing", f"ffmpeg not on PATH at {render_cfg.ffmpeg_path}")
        if ctx.storage is None:
            raise CapabilityUnsupported("storage-missing", "provider context has no storage")
        source = _materialize(payload.render_storage_key, ctx)
        results: list[ExportResponse] = []
        for fmt in payload.formats:
            codec = FORMAT_CODECS.get(fmt)
            if codec is None:
                continue
            output_path = str(Path(tempfile.gettempdir()) / "translator-export" / f"{os.urandom(8).hex()}.{fmt}")
            crf = render_cfg.crf_map.get(fmt, render_cfg.crf)
            cmd = [
                render_cfg.ffmpeg_path,
                "-y",
                "-i",
                source,
                "-c:v",
                codec["vcodec"],
                "-crf",
                str(crf),
                "-preset",
                render_cfg.preset,
                "-c:a",
                codec["acodec"],
                "-f",
                codec["container"],
                output_path,
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as exc:
                raise CapabilityUnsupported("ffmpeg-export-failed", exc.stderr.decode("utf-8", errors="ignore")[:512]) from exc
            with open(output_path, "rb") as fh:
                data = fh.read()
            if len(data) > cfg.max_size_bytes:
                raise CapabilityUnsupported("export-too-large", f"{fmt} exceeds max_size_bytes={cfg.max_size_bytes}")
            key = f"export/{self.id}/{Path(payload.render_storage_key).stem}.{fmt}"
            ctx.storage.upload(key, data, mime=f"video/{fmt}")
            digest = hashlib.sha256(data).hexdigest()
            results.append(
                ExportResponse(
                    export_id=None,
                    storage_key=key,
                    size_bytes=len(data),
                    checksum_sha256=digest,
                    format=fmt,
                    signature=self.fingerprint(payload),
                )
            )
        return results


def _materialize(storage_key: str, ctx: ProviderContext) -> str:
    if ctx.storage is None:
        raise CapabilityUnsupported("storage-missing", "provider context has no storage")
    tmp = Path(tempfile.gettempdir()) / "translator-export-input"
    tmp.mkdir(parents=True, exist_ok=True)
    target = tmp / Path(storage_key).name
    ctx.storage.download_to_path(storage_key, str(target))
    return str(target)
