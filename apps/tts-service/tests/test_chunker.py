"""Unit tests for the TTS microservice chunker, cache, and edge engine helpers."""

from __future__ import annotations

import pytest

from tts_service.cache import TtsLruCache
from tts_service.chunker import DEFAULT_MAX_CHARS, chunk_text
from tts_service.engines.edge import EdgeTtsEngine


class TestChunker:
    def test_short_text(self) -> None:
        assert chunk_text("Xin chào") == ["Xin chào"]

    def test_empty(self) -> None:
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_sentence_split(self) -> None:
        chunks = chunk_text("Câu một. Câu hai! Câu ba?", max_chars=12)
        # Each chunk is non-empty and starts with a capital Vietnamese letter
        # or with whitespace stripped away.
        for c in chunks:
            assert c
            assert c[0].isalpha()

    def test_max_chars_respected(self) -> None:
        chunks = chunk_text("a" * 1200 + "." + "b" * 200 + ".", max_chars=300)
        assert all(len(c) <= 300 for c in chunks)

    def test_overlong_sentence_hard_split(self) -> None:
        chunks = chunk_text("x" * 2500, max_chars=500)
        assert all(len(c) <= 500 for c in chunks)
        assert sum(len(c) for c in chunks) == 2500

    def test_default_max_chars(self) -> None:
        assert DEFAULT_MAX_CHARS == 500


class TestCache:
    def test_round_trip(self) -> None:
        cache = TtsLruCache(maxsize=4)
        cache.put("hi", "vi-VN-HoaiMyNeural", "+0%", "+0Hz", b"abc")
        assert cache.get("hi", "vi-VN-HoaiMyNeural", "+0%", "+0Hz") == b"abc"

    def test_miss(self) -> None:
        cache = TtsLruCache(maxsize=4)
        assert cache.get("missing", "vi", "+0%", "+0Hz") is None

    def test_eviction(self) -> None:
        cache = TtsLruCache(maxsize=2)
        cache.put("a", "vi", "+0%", "+0Hz", b"1")
        cache.put("b", "vi", "+0%", "+0Hz", b"2")
        cache.put("c", "vi", "+0%", "+0Hz", b"3")
        assert cache.get("a", "vi", "+0%", "+0Hz") is None
        assert cache.get("b", "vi", "+0%", "+0Hz") == b"2"

    def test_key_includes_all_params(self) -> None:
        cache = TtsLruCache(maxsize=8)
        cache.put("hi", "vi-VN-HoaiMyNeural", "+0%", "+0Hz", b"a")
        # Same text, different voice → different key.
        assert cache.get("hi", "vi-VN-NamMinhNeural", "+0%", "+0Hz") is None
        # Same text, different rate → different key.
        assert cache.get("hi", "vi-VN-HoaiMyNeural", "+25%", "+0Hz") is None

    def test_stats(self) -> None:
        cache = TtsLruCache(maxsize=4)
        cache.put("a", "vi", "+0%", "+0Hz", b"1")
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["maxsize"] == 4


class TestEdgeEngineHelpers:
    def test_resolve_alias(self) -> None:
        engine = EdgeTtsEngine()
        assert engine.resolve_voice("vi-female") == "vi-VN-HoaiMyNeural"
        assert engine.resolve_voice("vi-male") == "vi-VN-NamMinhNeural"
        assert engine.resolve_voice(None) == EdgeTtsEngine.DEFAULT_VOICE
        assert engine.resolve_voice("en-US-JennyNeural") == "en-US-JennyNeural"

    def test_format_rate(self) -> None:
        assert EdgeTtsEngine.format_rate(1.0) == "+0%"
        assert EdgeTtsEngine.format_rate(1.5) == "+50%"
        assert EdgeTtsEngine.format_rate(0.5) == "-50%"
        assert EdgeTtsEngine.format_rate(5.0) == "+100%"

    def test_format_pitch(self) -> None:
        assert EdgeTtsEngine.format_pitch(0.0) == "+0Hz"
        assert EdgeTtsEngine.format_pitch(50.0) == "+50Hz"
        assert EdgeTtsEngine.format_pitch(-50.0) == "-50Hz"
        assert EdgeTtsEngine.format_pitch(500.0) == "+100Hz"ê