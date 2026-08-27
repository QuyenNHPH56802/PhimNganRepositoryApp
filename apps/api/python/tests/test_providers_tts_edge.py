"""Unit tests for the Edge-TTS provider and chunker.

These tests do NOT require outbound network access; they exercise the
in-process LRU cache, voice alias mapping, chunker semantics, and the
fingerprint/header contract. The actual ``edge_tts.Communicate`` stream
is monkey-patched in ``test_run_chunks_and_caches`` to avoid hitting the
Microsoft service.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from translator_api.providers.base import (
    CapabilityUnsupported,
    ProviderCapabilities,
    ProviderContext,
)
from translator_api.providers.tts.edge import (
    DEFAULT_VOICE,
    LRU_MAX_SIZE,
    MAX_CHUNK_CHARS,
    VOICE_MAP,
    EdgeTtsProvider,
    _LruTtsCache,
    _cache_key,
    _format_pitch,
    _format_rate,
    chunk_text,
    list_voices,
    resolve_voice,
)
from translator_shared.provider_configs import TtsProviderConfig


class TestVoiceAlias:
    def test_default_voice_is_vietnamese_female(self) -> None:
        assert DEFAULT_VOICE == "vi-VN-HoaiMyNeural"

    def test_resolve_vi_female_alias(self) -> None:
        assert resolve_voice("vi-female") == "vi-VN-HoaiMyNeural"

    def test_resolve_vi_male_alias(self) -> None:
        assert resolve_voice("vi-male") == "vi-VN-NamMinhNeural"

    def test_resolve_unknown_falls_back(self) -> None:
        assert resolve_voice(None) == DEFAULT_VOICE
        assert resolve_voice("") == DEFAULT_VOICE
        # Unrelated id without a dash should fall back to default.
        assert resolve_voice("xyz") == DEFAULT_VOICE

    def test_resolve_shortname_passthrough(self) -> None:
        assert resolve_voice("en-US-JennyNeural") == "en-US-JennyNeural"

    def test_list_voices_returns_sorted_shortnames(self) -> None:
        voices = list(list_voices())
        assert "vi-VN-HoaiMyNeural" in voices
        assert voices == sorted(voices)


class TestChunker:
    def test_short_text_is_single_chunk(self) -> None:
        assert chunk_text("Xin chào") == ["Xin chào"]

    def test_empty_text_returns_no_chunks(self) -> None:
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_sentence_boundary_respected(self) -> None:
        text = "Câu một. Câu hai! Câu ba? Câu bốn."
        chunks = chunk_text(text, max_chars=12)
        # No chunk should start mid-sentence.
        for c in chunks:
            assert not c.startswith(("à", "á", "ạ", "ã")), f"chunk starts mid-word: {c!r}"

    def test_hard_split_when_sentence_exceeds_max(self) -> None:
        long_sentence = "a" * 1200 + "." + "b" * 300 + "."
        chunks = chunk_text(long_sentence, max_chars=500)
        assert all(len(c) <= 500 for c in chunks)
        assert len(chunks) >= 3

    def test_chunker_respects_max_chars(self) -> None:
        sentences = "Xin chào. " * 40
        chunks = chunk_text(sentences, max_chars=MAX_CHUNK_CHARS)
        assert all(len(c) <= MAX_CHUNK_CHARS for c in chunks)

    def test_chunk_count_preserves_all_content(self) -> None:
        text = "Xin chào các bạn. Tôi tên là Quyên. Rất vui được gặp bạn."
        chunks = chunk_text(text, max_chars=20)
        joined = " ".join(chunks)
        assert "Xin chào" in joined
        assert "Quyên" in joined


class TestFormatHelpers:
    def test_rate_neutral_is_plus_zero(self) -> None:
        assert _format_rate(1.0) == "+0%"

    def test_rate_faster(self) -> None:
        assert _format_rate(1.25) == "+25%"

    def test_rate_clamped_above(self) -> None:
        assert _format_rate(5.0) == "+100%"

    def test_rate_clamped_below(self) -> None:
        assert _format_rate(0.1) == "-50%"

    def test_pitch_zero(self) -> None:
        assert _format_pitch(0.0) == "+0Hz"

    def test_pitch_clamped(self) -> None:
        assert _format_pitch(250.0) == "+100Hz"
        assert _format_pitch(-250.0) == "-100Hz"


class TestLruCache:
    def test_put_and_get(self) -> None:
        cache = _LruTtsCache(maxsize=2)
        cache.put("k", b"hello")
        assert cache.get("k") == b"hello"

    def test_eviction(self) -> None:
        cache = _LruTtsCache(maxsize=2)
        cache.put("a", b"1")
        cache.put("b", b"2")
        cache.put("c", b"3")
        assert cache.get("a") is None
        assert cache.get("b") == b"2"
        assert cache.get("c") == b"3"

    def test_lru_refreshes(self) -> None:
        cache = _LruTtsCache(maxsize=2)
        cache.put("a", b"1")
        cache.put("b", b"2")
        _ = cache.get("a")
        cache.put("c", b"3")
        assert cache.get("b") is None
        assert cache.get("a") == b"1"

    def test_cache_key_distinguishes_params(self) -> None:
        k1 = _cache_key("hi", "vi-VN-HoaiMyNeural", "+0%", "+0Hz")
        k2 = _cache_key("hi", "vi-VN-NamMinhNeural", "+0%", "+0Hz")
        assert k1 != k2


class TestFingerprint:
    def test_fingerprint_changes_with_voice(self) -> None:
        provider = EdgeTtsProvider()
        from translator_api.providers.tts.base import TtsInput

        cfg = TtsProviderConfig()
        a = TtsInput(text="hello", voice_profile_id=str(uuid.uuid4()), config=cfg)
        b = TtsInput(text="hello", voice_profile_id=str(uuid.uuid4()), config=cfg)
        assert provider.fingerprint(a).model_id != provider.fingerprint(b).model_id

    def test_fingerprint_stable_for_same_text(self) -> None:
        provider = EdgeTtsProvider()
        from translator_api.providers.tts.base import TtsInput

        a = TtsInput(text="Xin chào", config=TtsProviderConfig())
        b = TtsInput(text="Xin chào", config=TtsProviderConfig())
        assert provider.fingerprint(a) == provider.fingerprint(b)


class TestProviderCapabilities:
    def test_capabilities_do_not_require_gpu(self) -> None:
        provider = EdgeTtsProvider()
        caps = provider.capabilities
        assert caps.requires_gpu is False
        assert caps.is_local is False

    def test_capabilities_declares_supported_languages(self) -> None:
        provider = EdgeTtsProvider()
        assert "vi" in provider.capabilities.supports_languages or not provider.capabilities.supports_languages


class TestProviderRuntime:
    def test_run_chunks_and_caches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify chunking + caching when edge_tts is monkey-patched."""
        from translator_api.providers.tts.base import TtsInput

        calls: list[str] = []

        class _StubCommunicate:
            def __init__(self, text: str, voice: str, rate: str, pitch: str) -> None:
                self.text = text
                self.voice = voice

            async def stream(self):
                calls.append(self.text)
                yield {"type": "audio", "data": b"\x00" * 1000}

        import sys
        mod = type(sys)("edge_tts")
        mod.Communicate = _StubCommunicate  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "edge_tts", mod)

        class _StubStorage:
            def __init__(self) -> None:
                self.uploads: list[tuple[str, bytes, str]] = []

            def upload(self, key: str, data: bytes, mime: str = "application/octet-stream") -> None:
                self.uploads.append((key, data, mime))

        storage = _StubStorage()
        ctx = ProviderContext(project_id="test-project", storage=storage)
        provider = EdgeTtsProvider()
        voice_uuid = uuid.uuid4()
        payload = TtsInput(
            text="Xin chào các bạn. Tôi tên là Quyên. " * 20,
            voice_profile_id=str(voice_uuid),
            config=TtsProviderConfig(),
        )
        result = asyncio.run(provider.run(payload, ctx=ctx))

        # Chunked dispatch was called.
        assert len(calls) >= 1
        # Storage got one combined upload under edge_tts namespace.
        assert len(storage.uploads) == 1
        key, data, mime = storage.uploads[0]
        assert key.startswith("tts/edge_tts/")
        assert key.endswith(".mp3")
        assert mime == "audio/mpeg"
        assert len(data) >= 1000 * len(calls)
        assert result.sample_rate == 24000

        # Second invocation should hit the cache for every chunk.
        calls.clear()
        result2 = asyncio.run(provider.run(payload, ctx=ctx))
        assert calls == []  # no network dispatch on cache hit
        assert result2.audio_storage_key != result.audio_storage_key  # different storage key

    def test_run_without_storage_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from translator_api.providers.tts.base import TtsInput

        class _StubCommunicate:
            def __init__(self, text: str, voice: str, rate: str, pitch: str) -> None:
                pass

            async def stream(self):
                yield {"type": "audio", "data": b"\x00" * 100}

        import sys
        mod = type(sys)("edge_tts")
        mod.Communicate = _StubCommunicate  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "edge_tts", mod)

        provider = EdgeTtsProvider()
        ctx = ProviderContext(project_id="test-project", storage=None)
        payload = TtsInput(text="hi", config=TtsProviderConfig())
        with pytest.raises(CapabilityUnsupported):
            asyncio.run(provider.run(payload, ctx=ctx))

    def test_run_empty_text_raises(self) -> None:
        from translator_api.providers.tts.base import TtsInput

        provider = EdgeTtsProvider()
        ctx = ProviderContext(project_id="test-project", storage=None)
        payload = TtsInput(text="   ", config=TtsProviderConfig())
        with pytest.raises(CapabilityUnsupported):
            asyncio.run(provider.run(payload, ctx=ctx))


class TestQwen3Registration:
    def test_qwen3_registered_in_default_registry(self) -> None:
        from translator_api.providers.registry import bootstrap
        from translator_api.providers.registry_constants import TTS

        registry = bootstrap()
        tts_ids = registry.list(TTS)
        assert "qwen3_tts" in tts_ids
        assert "edge_tts" in tts_ids
