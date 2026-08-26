"""Dubbing mixer — ffmpeg filter_complex + loudnorm."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MixerInput:
    speaker_audio_key: str
    bgm_audio_key: str | None
    output_storage_prefix: str = "dub"


@dataclass(frozen=True)
class MixerResult:
    output_path: str
    measured_lufs: float | None
    true_peak_dbtp: float | None
    ffmpeg_exit_code: int


def _which_ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise FileNotFoundError("ffmpeg binary not found on PATH")
    return binary


def mix_dub(
    speaker_path: Path,
    bgm_path: Path | None,
    *,
    output_dir: Path,
    target_lufs: float = -16.0,
    target_tp_dbtp: float = -1.0,
    sidechain_threshold: float = 0.05,
    sidechain_ratio: float = 8.0,
) -> MixerResult:
    """Mix `speaker_path` + `bgm_path` using ffmpeg sidechaincompress + loudnorm."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"dub_{os.urandom(8).hex()}.m4a"
    ffmpeg = _which_ffmpeg()

    if bgm_path is None:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(speaker_path),
            "-af",
            f"loudnorm=I={target_lufs}:LRA=11:TP={target_tp_dbtp}",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    else:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(speaker_path),
            "-i",
            str(bgm_path),
            "-filter_complex",
            (
                f"[1:a]volume=1.0[bgm];"
                f"[0:a][bgm]sidechaincompress=threshold={sidechain_threshold}:ratio={sidechain_ratio}:attack=5:release=200[compr];"
                f"[compr]loudnorm=I={target_lufs}:LRA=11:TP={target_tp_dbtp}[out]"
            ),
            "-map",
            "[out]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]

    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    measured_lufs, true_peak = _measure_loudness(output_path, ffmpeg)
    return MixerResult(
        output_path=str(output_path),
        measured_lufs=measured_lufs,
        true_peak_dbtp=true_peak,
        ffmpeg_exit_code=completed.returncode,
    )


def _measure_loudness(audio_path: Path, ffmpeg: str) -> tuple[float | None, float | None]:
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(audio_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    summary = completed.stderr
    lufs = _parse_field(summary, "Integrated loudness")
    peak = _parse_field(summary, "Peak level")
    return lufs, peak


def _parse_field(ebur_output: str, label: str) -> float | None:
    for line in ebur_output.splitlines():
        if label in line:
            tail = line.split(":")[-1].strip().split()
            try:
                return float(tail[0])
            except (ValueError, IndexError):
                return None
    return None


def loudness_delta(measured: float | None, target: float) -> float | None:
    if measured is None:
        return None
    return abs(measured - target)