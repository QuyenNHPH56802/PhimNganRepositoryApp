"""Synthetic data helpers.

Phase 5 helpers generate:
  * Vietnamese paraphrases by deterministic character substitution (for diff test
    cases that should NOT match the reference, to exercise BLEU/chrF).
  * Subtitle timing edge cases (long-line, short-line, overlap, empty).
  * TTS reference text placeholders.

Synthetic content is intentionally rough. It is *not* used to train models,
only to exercise metric formulas and CI smoke tests.
"""

from __future__ import annotations

import random


def paraphrase_vi(text: str, *, seed: int = 0) -> str:
    """Deterministically scramble punctuation and insert a typo to ensure BLEU drop.

    We deliberately avoid touching semantics so the result is still parsable
    Vietnamese, but `jiwer`/`sacrebleu` will record a regression.
    """

    rng = random.Random(seed + hash(text) & 0xFFFF)
    chars = list(text)
    if not chars:
        return text
    typo_index = rng.randrange(len(chars))
    chars[typo_index] = "x" if chars[typo_index] != "x" else "q"
    if rng.random() < 0.5:
        chars.append("!")
    return "".join(chars)


def subtitle_edge_cases() -> list[dict[str, object]]:
    return [
        {"name": "very_short", "start_ms": 0, "end_ms": 250, "vi": "OK.", "cps": 8.0},
        {"name": "very_long", "start_ms": 0, "end_ms": 8000, "vi": "Đây là một câu rất dài " * 4, "cps": 24.0},
        {"name": "overlap_first", "start_ms": 0, "end_ms": 2000, "vi": "Trước.", "cps": 16.0},
        {"name": "overlap_second", "start_ms": 1500, "end_ms": 3500, "vi": "Sau.", "cps": 16.0},
        {"name": "empty_text", "start_ms": 0, "end_ms": 1000, "vi": "", "cps": 0.0},
    ]


def tts_reference_text() -> list[str]:
    return [
        "Xin chào các bạn, tôi sẽ giới thiệu về chiếc điện thoại mới.",
        "Hôm nay chúng ta sẽ cùng tìm hiểu về lịch sử Việt Nam.",
        "Cảm ơn quý vị đã theo dõi, hẹn gặp lại trong chương trình sau.",
    ]