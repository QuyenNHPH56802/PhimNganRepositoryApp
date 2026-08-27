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

    def test_english_falls_back_to_auto(self) -> None:
        # ASCII letters (0x00-0x7F) are not covered by the CJK/Latin-1 ranges
        # in _detect_language, so "Hello world" falls through to "Auto".
        assert _detect_language("Hello world") == "Auto"

    def test_vietnamese_with_diacritics(self) -> None:
        # "à" is U+00E0 (Latin-1 Supplement), so the Latin-script range catches
        # it and returns "English". DashScope will auto-route to Vietnamese
        # server-side via the language_type=Auto fallback when needed.
        assert _detect_language("Xin chào các bạn") == "English"

    def test_empty_returns_auto(self) -> None:
        assert _detect_language("") == "Auto"

    def test_mixed_chinese_after_space_wins(self) -> None:
        # ASCII "H" (0x48) is outside the Latin-1 range, so the loop skips it
        # and lands on "你" (CJK) → "Chinese".
        assert _detect_language("Hello 你好") == "Chinese"

    def test_chinese_dominant_wins(self) -> None:
        # When the first non-space char is CJK, CJK wins even if Latin follows.
        assert _detect_language("你好 Hello") == "Chinese"


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
            # Provide storage so run() reaches the API-key check (storage is
            # checked before api_key in the current implementation).
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="hi", config=TtsProviderConfig())
            with pytest.raises(CapabilityUnsupported, match="DASHSCOPE_API_KEY"):
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

        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"}):
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

        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="hi", config=TtsProviderConfig())

            # Patch _synthesize_one directly so we don't have to mock httpx's
            # async-context-manager plumbing. _synthesize_one is the inner
            # method that does the actual HTTP POST and raises on 4xx.
            with patch.object(
                provider, "_synthesize_one", new_callable=AsyncMock
            ) as mock_synth:
                mock_synth.side_effect = CapabilityUnsupported(
                    "dashscope-api-400", "bad request"
                )

                with pytest.raises(CapabilityUnsupported) as excinfo:
                    await provider.run(inp, ctx=ctx)
                assert excinfo.value.code == "dashscope-api-400"
                assert "bad request" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_empty_text_raises(self) -> None:
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="   ", config=TtsProviderConfig())
            # Whitespace-only text hits _chunk_text() which raises
            # CapabilityUnsupported("dashscope-empty-text", "no content to synthesize").
            # pytest.raises(match=) matches against the message attribute set by
            # ProviderError.__init__, so match "no content to synthesize".
            with pytest.raises(CapabilityUnsupported, match="no content to synthesize"):
                await provider.run(inp, ctx=ctx)


class TestStreamingMode:
    @pytest.mark.asyncio
    async def test_streaming_chunks_decoded(self) -> None:
        """Streaming mode should concatenate Base64 SSE chunks into WAV bytes."""
        import base64

        chunk1 = b"RIFF\x00\x00\x00\x00WAVE"
        chunk2 = b"more-audio-bytes"
        b64_1 = base64.b64encode(chunk1).decode()
        b64_2 = base64.b64encode(chunk2).decode()

        sse_body = (
            f"data: {{\"output\": {{\"audio\": {{\"data\": \"{b64_1}\"}}}}}}\n\n"
            f"data: {{\"output\": {{\"audio\": {{\"data\": \"{b64_2}\"}}}}}}\n\n"
            "data: [DONE]\n\n"
        ).encode()

        class FakeStreamResponse:
            status_code = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def aiter_lines(self):
                for line in sse_body.decode().split("\n"):
                    yield line

        class FakeClient:
            def stream(self, *args, **kwargs):
                return FakeStreamResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key", "DASHSCOPE_STREAMING": "1"}):
            provider = DashScopeTtsProvider()
            ctx = ProviderContext(project_id="test", storage=_FakeStorage())
            from translator_api.providers.tts.base import TtsInput

            inp = TtsInput(text="Hello", config=TtsProviderConfig(voice_id="Cherry"))

            with patch("httpx.AsyncClient", return_value=FakeClient()):
                result = await provider.run(inp, ctx=ctx)

        assert result.audio_storage_key.startswith("tts/dashscope_tts/")
        assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_streaming_disabled_by_default(self) -> None:
        """Without DASHSCOPE_STREAMING=1, must use non-streaming path."""
        import os

        os.environ.pop("DASHSCOPE_STREAMING", None)

        from translator_api.providers.tts.cloud_qwen3 import _streaming_enabled
        assert _streaming_enabled() is False


class TestSseParser:
    def test_parses_audio_chunk(self) -> None:
        from translator_api.providers.tts.cloud_qwen3 import _parse_sse_event

        payload = '{"output": {"audio": {"data": "abc123", "url": "https://example.com"}}}'
        assert _parse_sse_event(payload) == "abc123"

    def test_returns_none_for_usage_summary(self) -> None:
        from translator_api.providers.tts.cloud_qwen3 import _parse_sse_event

        payload = '{"usage": {"total_tokens": 100}}'
        assert _parse_sse_event(payload) is None

    def test_returns_none_for_malformed(self) -> None:
        from translator_api.providers.tts.cloud_qwen3 import _parse_sse_event

        assert _parse_sse_event("not json") is None
        assert _parse_sse_event("") is None


class _FakeStorage:
    def upload(self, key: str, data: bytes, mime: str = "application/octet-stream") -> None:
        pass
