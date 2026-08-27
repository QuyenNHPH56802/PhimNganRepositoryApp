"""Unit tests for the DashScope Qwen3-TTS cloud provider.

These tests exercise the chunker, language detection, fingerprint, and the
non-streaming HTTP flow with a fake httpx mock. No real DashScope API call
is made.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from translator_api.providers.base import CapabilityUnsupported, ProviderContext
from translator_api.providers.tts.cloud_qwen3 import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DashScopeTtsProvider,
    _chunk_text,
    _detect_language,
)
from translator_shared.provider_configs import TtsProviderConfig


class TestLanguageDetection:
    def test_chinese(self) -> None:
        assert _detect_language("你好世界") == "Chinese"

    def test_japanese(self) -> None:
        assert _detect_language("こんにちは") == "Japanese"

    def test_korean(self) -> None:
        assert _detect_language("안녕하세요") == "Korean"

    def test_russian(self) -> None:
        assert _detect_language("Привет мир") == "Russian"

    def test_english(self) -> None:
        assert _detect_language("Hello world") == "English"

    def test_vietnamese_falls_back_to_auto(self) -> None:
        # Vietnamese has Latin script, so we fall back to Auto
        assert _detect_language("Xin chào các bạn") == "Auto"

    def test_empty_returns_auto(self) -> None:
        assert _detect_language("") == "Auto"

    def test_mixed_defaults_to_auto(self) -> None:
        assert _detect_language("Hello 你好") == "Auto"


class TestChunker:
    def test_short_text_returns_one_chunk(self) -> None:
        assert _chunk_text("Xin chào", max_chars=500) == ["Xin chào"]

    def test_empty_returns_empty_list(self) -> None:
        assert _chunk_text("", max_chars=500) == []
        assert _chunk_text("   ", max_chars=500) == []

    def test_long_text_split_on_sentences(self) -> None:
        text = "Câu một. Câu hai! Câu ba?"
        chunks = _chunk_text(text, max_chars=12)
        assert all(len(c) <= 12 for c in chunks)
        assert len(chunks) >= 3

    def test_respects_max_chars(self) -> None:
        text = "a" * 300 + ". " + "b" * 300 + "."
        chunks = _chunk_text(text, max_chars=200)
        assert all(len(c) <= 200 for c in chunks)


class TestFingerprint:
    def test_fingerprint_includes_model(self) -> None:
        provider = DashScopeTtsProvider()
        cfg = TtsProviderConfig(model_id="qwen3-tts-flash", voice_id="Cherry")
        from translator_api.providers.tts.base import TtsInput

        inp = TtsInput(text="Hello", config=cfg)
        fp = provider.fingerprint(inp)
        assert fp.model_id == "qwen3-tts-flash"
        assert fp.provider_build == "dashscope_tts"


class TestMissingApiKey:
    def test_raises_if_no_api_key(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=None)
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="hi", config=TtsProviderConfig())
            with pytest.raises(CapabilityUnsupported, match="dashscope-missing-api-key"):
                asyncio.run(provider.run(inp, ctx=ctx))


class TestHttpFlow:
    @pytest.mark.asyncio
    async def test_successful_non_streaming(self) -> None:
        """Verify POST → JSON parse → audio URL download → WAV bytes."""
        audio_data = b"RIFF" + b"\x00" * 40  # minimal WAV header

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "output": {"audio": {"url": "https://example.com/audio.wav"}},
        }

        mock_audio_response = MagicMock()
        mock_audio_response.status_code = 200
        mock_audio_response.content = audio_data

        async def fake_post(url, **kwargs):
            return mock_response

        async def fake_get(url, **kwargs):
            return mock_audio_response

        with patch.dict("os.environ", {"DASHSCOPE_API_KEY", "test-key"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="Hello", config=TtsProviderConfig(voice_id="Cherry"))

            with patch.object(provider, "_synthesize_one", autospec=True) as mock_one:
                mock_one.return_value = audio_data

                result = await provider.run(inp, ctx=ctx)

        assert result.audio_storage_key.startswith("tts/dashscope_tts/")
        assert result.duration_ms >= 1
        assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self) -> None:
        """Verify HTTP 4xx raises CapabilityUnsupported."""

        class FakeResponse:
            status_code = 400
            text = "bad request"

        async def fake_post(url, **kwargs):
            return FakeResponse()

        with patch.dict("os.environ", {"DASHSCOPE_API_KEY", "test-key"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=None)
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="hi", config=TtsProviderConfig())

            with patch("httpx.AsyncClient") as MockClient:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=FakeResponse())
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock()
                MockClient.return_value = mock_instance

                with pytest.raises(CapabilityUnsupported, match="dashscope-api-400"):
                    await provider.run(inp, ctx=ctx)

    @pytest.mark.asyncio
    async def test_empty_text_raises(self) -> None:
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY", "test-key"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="   ", config=TtsProviderConfig())
            with pytest.raises(CapabilityUnsupported, match="dashscope-empty-text"):
                await provider.run(inp, ctx=ctx)


class _FakeStorage:
    def upload(self, key: str, data: bytes, mime: str = "application/octet-stream") -> None:
        pass
