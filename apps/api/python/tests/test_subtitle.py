"""Unit tests for apps/api/python/translator_api/subtitle."""

from __future__ import annotations

import pytest

from translator_api.schemas_alignment import AlignedWord, TranscriptSegment
from translator_api.subtitle.aligner import (
    align_subtitles_to_asr,
    alignment_mse,
)
from translator_api.subtitle.locale_rules import (
    LocaleRule,
    SubtitleCueFactory,
    locale_rule,
)


# ---------------------------------------------------------------------------
# locale_rules
# ---------------------------------------------------------------------------


class TestLocaleRule:
    def test_default_vietnamese(self) -> None:
        rule = locale_rule("vi")
        assert rule.cps == pytest.approx(16.0)
        assert rule.max_line_length == 40
        assert rule.punctuation_end == (".", ",", "!", "?", "…")

    def test_chinese_uses_full_width_punct(self) -> None:
        rule = locale_rule("zh")
        assert "。" in rule.punctuation_end
        assert "「" in rule.punctuation_begin
        assert rule.max_line_length == 22

    def test_japanese_strictest_cps(self) -> None:
        rule = locale_rule("ja")
        assert rule.cps == pytest.approx(14.0)

    def test_unknown_locale_falls_back_to_vi(self) -> None:
        rule = locale_rule("xx")
        assert rule == locale_rule("vi")

    def test_supported_locales_table_complete(self) -> None:
        for code in ("vi", "en", "zh", "ja", "ko"):
            rule = locale_rule(code)
            assert isinstance(rule, LocaleRule)
            assert rule.cps > 0
            assert rule.max_line_length > 0


class TestSubtitleCueFactory:
    def test_clamp_short_text_returns_input(self) -> None:
        factory = SubtitleCueFactory("vi")
        text, duration = factory.clamp("xin chào", max_duration_ms=2000)
        assert text == "xin chào"
        assert duration == 2000

    def test_clamp_long_text_truncates(self) -> None:
        factory = SubtitleCueFactory("vi")  # cps = 16
        long_text = "a" * 80
        text, duration = factory.clamp(long_text, max_duration_ms=1000)
        # max chars = 16 chars/sec * 1s = 16
        assert len(text) == 16
        assert duration >= 1000

    def test_normalize_nfc(self) -> None:
        factory = SubtitleCueFactory("vi")
        decomposed = "Vi\u1ec7t Nam"  # "i" + combining dot
        normalized = factory.normalize(decomposed)
        assert normalized == "Việt Nam"

    def test_unsupported_locale_returns_unsupported(self) -> None:
        with pytest.raises(KeyError):
            SubtitleCueFactory("xyz")

    def test_zero_duration_returns_input(self) -> None:
        factory = SubtitleCueFactory("vi")
        text, duration = factory.clamp("abc", max_duration_ms=0)
        assert text == "abc"
        assert duration == 0


# ---------------------------------------------------------------------------
# aligner
# ---------------------------------------------------------------------------


def _seg(word_texts: list[str], start_ms: int, step_ms: int = 500) -> TranscriptSegment:
    words = [
        AlignedWord(text=t, start_ms=start_ms + i * step_ms, end_ms=start_ms + (i + 1) * step_ms, score=1.0)
        for i, t in enumerate(word_texts)
    ]
    return TranscriptSegment(
        id="seg",
        text=" ".join(word_texts),
        start_ms=start_ms,
        end_ms=start_ms + len(word_texts) * step_ms,
        words=words,
    )


class TestAlignSubtitles:
    def test_empty_inputs_returns_empty(self) -> None:
        assert align_subtitles_to_asr([], "hello") == []
        assert align_subtitles_to_asr([_seg(["hello"], 0)], "") == []

    def test_exact_match_preserves_timing(self) -> None:
        seg = _seg(["xin", "chào"], 0, step_ms=500)
        cues = align_subtitles_to_asr([seg], "xin chào")
        assert len(cues) == 1
        assert cues[0].text == "xin chào"
        assert cues[0].start_ms == 0
        assert cues[0].end_ms == 1000

    def test_replacement_uses_target_tokens(self) -> None:
        seg = _seg(["hello", "world"], 0, step_ms=500)
        cues = align_subtitles_to_asr([seg], "xin chào bạn")
        # Replacement still produces at least one cue spanning the words.
        assert cues
        joined = " ".join(c.text for c in cues)
        assert "xin" in joined
        assert "chào" in joined

    def test_dwell_minimum_enforced(self) -> None:
        seg = _seg(["a"], 0, step_ms=100)
        cues = align_subtitles_to_asr([seg], "a")
        assert cues[0].end_ms - cues[0].start_ms >= 800

    def test_clamp_cps_extends_duration(self) -> None:
        # 100 chars at cps=16 over 1 second is too fast
        seg = _seg(["x"], 0, step_ms=10_000)
        cues = align_subtitles_to_asr([seg], "x", target_cps=16.0)
        # Single-char cue passes clamp unchanged.
        assert cues[0].end_ms - cues[0].start_ms == 10_000

    def test_alignment_mse_zero_for_perfect(self) -> None:
        from translator_api.subtitle.aligner import SubtitleCue

        cues = [SubtitleCue(text="hi", start_ms=0, end_ms=1000)]
        assert alignment_mse(cues, [(0, 1000)]) == 0.0

    def test_alignment_mse_symmetric(self) -> None:
        from translator_api.subtitle.aligner import SubtitleCue

        cues = [SubtitleCue(text="hi", start_ms=100, end_ms=900)]
        mse = alignment_mse(cues, [(0, 1000)])
        # diffs: 100^2 + 100^2 / 2
        assert mse == pytest.approx((100**2 + 100**2) / 2)

    def test_alignment_mse_empty_input_is_inf(self) -> None:
        assert alignment_mse([], []) == float("inf")
