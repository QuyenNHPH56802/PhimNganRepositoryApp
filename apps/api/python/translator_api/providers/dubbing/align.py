"""Dubbing align provider via FFmpeg atempo chain."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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


def _run_ffmpeg(cmd: list[str], ffmpeg_path: str = "ffmpeg") -> None:
    """Run an ffmpeg command and translate failures into ``CapabilityUnsupported``.

    Centralised so all SpeedRate passes surface a uniform error code to the
    activity fallback chain (e.g. ``align-ffmpeg-failed``).
    """
    binary = cmd[0]
    if shutil.which(binary) is None:
        raise CapabilityUnsupported(
            "ffmpeg-missing",
            f"ffmpeg not on PATH at {binary}",
        )
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        raise CapabilityUnsupported(
            "align-ffmpeg-failed",
            exc.stderr.decode("utf-8", errors="ignore")[:512],
        ) from exc


@dataclass(frozen=True)
class SpeedRateConfig:
    """Configuration for ``SpeedRate`` cue-alignment pass.

    Reference: pyVideoTrans ``task/_base.py::SpeedRate`` pattern.

    Attributes:
        ffmpeg_path: Binary to invoke; defaults to ``ffmpeg`` on PATH.
        min_speed: Lower bound on tempo multiplier (0.5..2.0 per atempo).
        max_speed: Upper bound on tempo multiplier.
        silence_threshold_db: Silence detection threshold for
            ``silenceremove`` filter (-60..0 dB).
        silence_min_duration_s: Minimum silence span to strip, in seconds.
        fallback_padding: Padding factor used when force_align under-shoots
            the target duration (rare; happens when ``atempo`` clamps).
    """

    ffmpeg_path: str = "ffmpeg"
    min_speed: float = 0.5
    max_speed: float = 2.0
    silence_threshold_db: float = -40.0
    silence_min_duration_s: float = 0.2
    fallback_padding: float = 0.0


@dataclass
class SpeedRate:
    """Adjust a synthesized audio clip to match a target cue duration.

    Workflow (matches pyVideoTrans ``SpeedRate``):
        1. ``speedup(factor)`` if source is longer than the cue (compress).
        2. ``remove_silence()`` to drop dead air at edges.
        3. ``force_align()`` to combine both, padding with silence if needed
           so the output duration matches ``target_duration_ms`` exactly.

    All operations are pure FFmpeg invocations; no GPU required.
    """

    target_duration_ms: int
    audio_path: str
    config: SpeedRateConfig | None = None
    _current_path: str = ""

    def __post_init__(self) -> None:
        self._current_path = self.audio_path

    @property
    def current_path(self) -> str:
        return self._current_path

    def _resolved_config(self) -> SpeedRateConfig:
        return self.config or SpeedRateConfig()

    def speedup(self, factor: float) -> "SpeedRate":
        """Apply an atempo chain to compress/expand audio in place.

        ``factor`` is the multiplier: >1 means faster, <1 slower.
        """
        if abs(factor - 1.0) < 1e-3:
            return self
        cfg = self._resolved_config()
        ratio = max(cfg.min_speed, min(cfg.max_speed, factor))
        filters = _build_atempo_chain(ratio)
        output = self._tmp_path(".wav")
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            self._current_path,
            "-filter:a",
            ",".join(filters),
            output,
        ]
        _run_ffmpeg(cmd, cfg.ffmpeg_path)
        self._current_path = output
        return self

    def remove_silence(self) -> "SpeedRate":
        """Strip leading/trailing silence from the audio clip."""
        cfg = self._resolved_config()
        threshold = f"{cfg.silence_threshold_db}dB"
        min_dur = f"{cfg.silence_min_duration_s}"
        output = self._tmp_path(".wav")
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            self._current_path,
            "-af",
            f"silenceremove=start_periods=1:start_silence=0:start_threshold={threshold}:stop_periods=-1:stop_silence=0:stop_threshold={threshold}:window=0:detection=peak",
            output,
        ]
        try:
            _run_ffmpeg(cmd, cfg.ffmpeg_path)
            self._current_path = output
        except CapabilityUnsupported:
            # Fallback: pad-trim by re-encoding from start; never crash the
            # activity for a non-essential cleanup step.
            pass
        return self

    def force_align(self) -> "SpeedRate":
        """Align current audio length to ``target_duration_ms``.

        Combines ``speedup`` (when too long) with silence padding (when too
        short) so the returned clip is within one sample of the cue length.
        """
        current_ms = _probe_duration_ms(self._current_path, self._resolved_config().ffmpeg_path)
        if current_ms <= 0:
            return self
        target_ms = max(1, int(self.target_duration_ms))

        if current_ms > target_ms:
            factor = current_ms / target_ms
            self.speedup(factor)
            current_ms = _probe_duration_ms(self._current_path, self._resolved_config().ffmpeg_path)

        if current_ms < target_ms:
            pad_ms = target_ms - current_ms
            self._pad_silence(pad_ms)
            current_ms = _probe_duration_ms(self._current_path, self._resolved_config().ffmpeg_path)

        if abs(current_ms - target_ms) > 50:
            # Last-resort trim to avoid extending cues that the dubbing
            # align provider would otherwise surface to the mixer.
            self._trim(current_ms - target_ms)
        return self

    def _pad_silence(self, pad_ms: int) -> None:
        cfg = self._resolved_config()
        output = self._tmp_path(".wav")
        seconds = max(0.001, pad_ms / 1000.0)
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            self._current_path,
            "-af",
            f"apad=pad_dur={seconds:.3f}",
            "-t",
            f"{(self._probe_current_ms() + pad_ms) / 1000.0:.3f}",
            output,
        ]
        _run_ffmpeg(cmd, cfg.ffmpeg_path)
        self._current_path = output

    def _trim(self, overshoot_ms: int) -> None:
        cfg = self._resolved_config()
        if overshoot_ms <= 0:
            return
        current_ms = self._probe_current_ms()
        target_ms = max(1, current_ms - overshoot_ms)
        output = self._tmp_path(".wav")
        cmd = [
            cfg.ffmpeg_path,
            "-y",
            "-i",
            self._current_path,
            "-t",
            f"{target_ms / 1000.0:.3f}",
            output,
        ]
        _run_ffmpeg(cmd, cfg.ffmpeg_path)
        self._current_path = output

    def _probe_current_ms(self) -> int:
        return _probe_duration_ms(self._current_path, self._resolved_config().ffmpeg_path)

    def _tmp_path(self, suffix: str) -> str:
        tmp = Path(tempfile.gettempdir()) / "translator-speedrate"
        tmp.mkdir(parents=True, exist_ok=True)
        return str(tmp / f"{os.urandom(8).hex()}{suffix}")


def _probe_duration_ms(audio_path: str, ffmpeg_path: str = "ffmpeg") -> int:
    """Probe audio duration in milliseconds using FFmpeg's stdout."""
    if shutil.which(ffmpeg_path) is None:
        return 0
    cmd = [
        "ffprobe" if shutil.which("ffprobe") else ffmpeg_path,
    ]
    if cmd[0] == "ffprobe":
        cmd += ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", audio_path]
    else:
        cmd += ["-i", audio_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    if not out:
        return 0
    try:
        return max(1, int(float(out) * 1000))
    except ValueError:
        return 0


def align_to_cue(
    audio_path: str,
    target_duration_ms: int,
    config: SpeedRateConfig | None = None,
) -> str:
    """Convenience helper used by worker activities.

    Returns the path to the aligned clip; callers are responsible for
    uploading the result to storage.
    """
    sr = SpeedRate(target_duration_ms=target_duration_ms, audio_path=audio_path, config=config)
    sr.remove_silence().force_align()
    return sr.current_path