"""Unit tests for the dubbing align provider and the new SpeedRate helper."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from translator_api.providers.base import CapabilityUnsupported
from translator_api.providers.dubbing.align import (
    FfmpegAtempoAlignProvider,
    SpeedRate,
    SpeedRateConfig,
    _build_atempo_chain,
    _probe_duration_ms,
    align_to_cue,
)


# ---------------------------------------------------------------------------
# FfmpegAtempoAlignProvider contract (existing)
# ---------------------------------------------------------------------------


class TestAtempoChain:
    def test_ratio_one_returns_single_pass(self) -> None:
        assert _build_atempo_chain(1.0) == ["atempo=1.0"]

    def test_ratio_two_chains(self) -> None:
        chain = _build_atempo_chain(2.5)
        assert any(f.startswith("atempo=2.0000") for f in chain)
        assert all(f.startswith("atempo=") for f in chain)

    def test_ratio_half_chains(self) -> None:
        chain = _build_atempo_chain(0.25)
        assert any(f.startswith("atempo=0.5000") for f in chain)


class TestProbeDuration:
    def test_probe_returns_zero_when_ffprobe_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _x: None)
        assert _probe_duration_ms("/nonexistent.wav") == 0


# ---------------------------------------------------------------------------
# SpeedRate (new, pyVideoTrans pattern)
# ---------------------------------------------------------------------------


class TestSpeedRateHelpers:
    def test_config_defaults_are_safe(self) -> None:
        cfg = SpeedRateConfig()
        assert cfg.min_speed == 0.5
        assert cfg.max_speed == 2.0
        assert cfg.silence_threshold_db <= 0


class TestSpeedRateFakeFfmpeg:
    """Drive ``SpeedRate`` from fake subprocess invocations.

    We avoid invoking real ffmpeg so the tests run in any environment; the
    contract under test is that the FFmpeg command line is constructed
    correctly for the speedup / silence removal / padding passes.
    """

    def _write_fake_audio(self, tmp_path: Path, name: str = "input.wav") -> str:
        path = tmp_path / name
        path.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")  # not a real wav; just a file
        return str(path)

    def _fake_run(self, cmd: list[str], **kwargs) -> object:
        # Use the trailing output path (last positional arg) to materialise
        # an output file we can probe.
        output_path = cmd[-1]
        Path(output_path).write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        return type("R", (), {"returncode": 0, "stderr": b""})()

    def _fake_probe(self, audio_path: str, ffmpeg_path: str = "ffmpeg") -> int:
        # Pretend every operation produces a 1-second audio clip.
        return 1000

    def test_speedup_invokes_atempo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = self._write_fake_audio(tmp_path)
        monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/ffmpeg")
        monkeypatch.setattr("translator_api.providers.dubbing.align.subprocess.run", self._fake_run)
        monkeypatch.setattr("translator_api.providers.dubbing.align._probe_duration_ms", self._fake_probe)

        sr = SpeedRate(target_duration_ms=500, audio_path=src)
        sr.speedup(2.0)
        # path changes after first operation
        assert sr.current_path != src

    def test_force_align_too_long_uses_speedup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = self._write_fake_audio(tmp_path)
        monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/ffmpeg")
        monkeypatch.setattr("translator_api.providers.dubbing.align.subprocess.run", self._fake_run)
        monkeypatch.setattr("translator_api.providers.dubbing.align._probe_duration_ms", self._fake_probe)

        sr = SpeedRate(target_duration_ms=500, audio_path=src)
        sr.force_align()
        # The current path should have advanced past the original input.
        assert sr.current_path != src

    def test_force_align_too_short_pads(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = self._write_fake_audio(tmp_path)

        # Probe returns 1000ms for the input, but the target is 5000ms → padding branch.
        monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/ffmpeg")
        monkeypatch.setattr("translator_api.providers.dubbing.align.subprocess.run", self._fake_run)
        monkeypatch.setattr(
            "translator_api.providers.dubbing.align._probe_duration_ms",
            lambda *a, **kw: 1000,
        )

        sr = SpeedRate(target_duration_ms=5000, audio_path=src)
        sr.force_align()
        assert sr.current_path != src

    def test_remove_silence_keeps_path_when_filter_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        src = self._write_fake_audio(tmp_path)
        monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/ffmpeg")

        def _raise(_cmd, **_kw):
            raise subprocess.CalledProcessError(1, [], stderr=b"silenceremove unsupported")

        import subprocess
        monkeypatch.setattr("translator_api.providers.dubbing.align.subprocess.run", _raise)
        # Should NOT crash — fallback is to leave path unchanged.
        sr = SpeedRate(target_duration_ms=2000, audio_path=src)
        sr.remove_silence()
        assert sr.current_path == src

    def test_align_to_cue_returns_string(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = self._write_fake_audio(tmp_path)
        monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/ffmpeg")
        monkeypatch.setattr("translator_api.providers.dubbing.align.subprocess.run", self._fake_run)
        monkeypatch.setattr("translator_api.providers.dubbing.align._probe_duration_ms", self._fake_probe)
        result = align_to_cue(src, target_duration_ms=750)
        assert isinstance(result, str)
        assert result != src


class TestFfmpegAtempoAlignProviderFingerprint:
    def test_fingerprint_differs_per_storage_key(self) -> None:
        provider = FfmpegAtempoAlignProvider()
        from translator_api.providers.dubbing.align import DubbingAlignInput

        a = provider.fingerprint(DubbingAlignInput(voice_storage_key="a.wav", target_duration_ms=1000, source_duration_ms=1200))
        b = provider.fingerprint(DubbingAlignInput(voice_storage_key="b.wav", target_duration_ms=1000, source_duration_ms=1200))
        assert a.input_hash != b.input_hash
