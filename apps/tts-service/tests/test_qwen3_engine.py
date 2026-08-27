"""Unit tests for the Qwen3-TTS adapter."""

from __future__ import annotations

import asyncio
import sys
import types

import pytest

from tts_service.engines.qwen3 import Qwen3Request, Qwen3TtsEngine


class _FakeAudio:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def tobytes(self) -> bytes:
        return self._payload


def _install_fake_qwen_tts(monkeypatch, payload: bytes = b"RIFF\x00\x00\x00\x00WAVE") -> None:
    """Install a stub ``qwen_tts`` module so warmup succeeds."""

    fake_mod = types.ModuleType("qwen_tts")

    class _FakeModel:
        def synthesize(self, *, text: str, voice: str, speed: float, pitch: float, sample_rate: int) -> _FakeAudio:
            return _FakeAudio(payload)

    fake_mod.Qwen3TTS = lambda model_id: _FakeModel()  # noqa: ARG005
    monkeypatch.setitem(sys.modules, "qwen_tts", fake_mod)


class TestQwen3VoiceResolution:
    def test_default_voice(self) -> None:
        engine = Qwen3TtsEngine()
        assert engine.resolve_voice(None) == Qwen3TtsEngine.DEFAULT_VOICE

    def test_aliases(self) -> None:
        engine = Qwen3TtsEngine()
        assert engine.resolve_voice("vi-female") == "qwen-vi-female"
        assert engine.resolve_voice("vi-male") == "qwen-vi-male"
        assert engine.resolve_voice("en-female") == "qwen-en-female"
        assert engine.resolve_voice("zh-female") == "qwen-zh-female"

    def test_unknown_voice_passthrough(self) -> None:
        engine = Qwen3TtsEngine()
        assert engine.resolve_voice("custom-voice") == "custom-voice"


class TestQwen3Warmup:
    def test_warmup_without_sdk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "qwen_tts", None)
        engine = Qwen3TtsEngine()
        engine.warmup()
        assert engine.is_ready() is False

    def test_warmup_with_fake_sdk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_qwen_tts(monkeypatch)
        engine = Qwen3TtsEngine()
        engine.warmup()
        assert engine.is_ready() is True


class TestQwen3Synthesize:
    @pytest.mark.asyncio
    async def test_synthesize_returns_bytes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_qwen_tts(monkeypatch, payload=b"FAKE_WAV_DATA")
        engine = Qwen3TtsEngine()
        engine.warmup()
        assert engine.is_ready()
        audio = await engine.synthesize(
            Qwen3Request(text="Xin chào", voice="qwen-vi-female", speed=1.0, pitch=0.0, sample_rate=24000)
        )
        assert audio == b"FAKE_WAV_DATA"

    @pytest.mark.asyncio
    async def test_synthesize_without_model_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "qwen_tts", None)
        engine = Qwen3TtsEngine()
        with pytest.raises(RuntimeError, match="qwen3-tts-checkpoint-missing"):
            await engine.synthesize(
                Qwen3Request(text="Xin chào", voice="qwen-vi-female")
            )

    @pytest.mark.asyncio
    async def test_synthesize_concurrent_warmup_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_qwen_tts(monkeypatch, payload=b"WAV")
        engine = Qwen3TtsEngine()
        results = await asyncio.gather(
            engine.synthesize(Qwen3Request(text="a", voice="qwen-vi-female")),
            engine.synthesize(Qwen3Request(text="b", voice="qwen-vi-female")),
            engine.synthesize(Qwen3Request(text="c", voice="qwen-vi-female")),
        )
        assert results == [b"WAV", b"WAV", b"WAV"]
        assert engine.is_ready()

    @pytest.mark.asyncio
    async def test_synthesize_propagates_runtime_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_mod = types.ModuleType("qwen_tts")

        class _Broken:
            def synthesize(self, **_kwargs):
                raise OSError("model file missing")

        fake_mod.Qwen3TTS = lambda model_id: _Broken()  # noqa: ARG005
        monkeypatch.setitem(sys.modules, "qwen_tts", fake_mod)
        engine = Qwen3TtsEngine()
        engine.warmup()
        with pytest.raises(RuntimeError, match="qwen3-synthesis-failed"):
            await engine.synthesize(Qwen3Request(text="hi", voice="qwen-vi-female"))

    @pytest.mark.asyncio
    async def test_synthesize_handles_bytearray(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_mod = types.ModuleType("qwen_tts")

        class _Model:
            def synthesize(self, **_kwargs):
                return bytearray(b"abc")

        fake_mod.Qwen3TTS = lambda model_id: _Model()  # noqa: ARG005
        monkeypatch.setitem(sys.modules, "qwen_tts", fake_mod)
        engine = Qwen3TtsEngine()
        engine.warmup()
        audio = await engine.synthesize(Qwen3Request(text="hi", voice="qwen-vi-female"))
        assert audio == b"abc"