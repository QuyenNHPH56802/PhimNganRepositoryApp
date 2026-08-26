"""Subtitle alignment.

Phase 7 maps ASR tokens to a target cue stream via dynamic programming
(insertion/substitution/deletion costs) so the resulting subtitle timing
matches the source language timing as closely as possible. The
`align_subtitles_to_asr` function is deterministic and CI-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from translator_api.schemas_alignment import TranscriptSegment


@dataclass(frozen=True)
class SubtitleCue:
    text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class AsrWord:
    text: str
    start_ms: int
    end_ms: int
    speaker_id: str | None = None


def align_subtitles_to_asr(
    asr_segments: list[TranscriptSegment],
    target_text: str,
    *,
    target_cps: float = 16.0,
    min_dwell_ms: int = 800,
    gap_padding_ms: int = 80,
) -> list[SubtitleCue]:
    asr_words: list[AsrWord] = [
        AsrWord(text=w.text, start_ms=w.start_ms, end_ms=w.end_ms, speaker_id=w.speaker_id)
        for seg in asr_segments
        for w in seg.words
    ]
    target_tokens = target_text.split()
    if not asr_words or not target_tokens:
        return []

    matcher = SequenceMatcher(a=[w.text for w in asr_words], b=target_tokens)
    cues: list[SubtitleCue] = []
    pending_tokens: list[str] = []
    pending_start_ms = asr_words[0].start_ms
    pending_end_ms = pending_start_ms

    def flush(end_ms: int) -> None:
        nonlocal pending_tokens, pending_start_ms, pending_end_ms
        if not pending_tokens:
            return
        end = max(end_ms, pending_start_ms + min_dwell_ms)
        cues.append(SubtitleCue(text=" ".join(pending_tokens), start_ms=pending_start_ms, end_ms=end))
        pending_tokens = []
        pending_start_ms = end_ms + gap_padding_ms
        pending_end_ms = pending_start_ms

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(j2 - j1):
                target_word = target_tokens[j1 + offset]
                word = asr_words[i1 + offset] if i1 + offset < len(asr_words) else None
                if word is None:
                    continue
                pending_tokens.append(target_word)
                pending_end_ms = word.end_ms
        elif tag == "replace":
            span_start_ms = asr_words[i1].start_ms if i1 < len(asr_words) else pending_start_ms
            span_end_ms = asr_words[min(i2 - 1, len(asr_words) - 1)].end_ms if i1 < len(asr_words) else pending_end_ms
            for offset in range(j2 - j1):
                pending_tokens.append(target_tokens[j1 + offset])
                pending_end_ms = span_end_ms
            pending_start_ms = span_start_ms
        elif tag == "insert":
            for offset in range(j2 - j1):
                pending_tokens.append(target_tokens[j1 + offset])
        elif tag == "delete":
            flush(asr_words[min(i2 - 1, len(asr_words) - 1)].end_ms)
            pending_start_ms = asr_words[i2].start_ms if i2 < len(asr_words) else pending_start_ms
            pending_end_ms = pending_start_ms

    flush(pending_end_ms)
    return _clamp_cps(cues, target_cps=target_cps)


def _clamp_cps(cues: list[SubtitleCue], *, target_cps: float) -> list[SubtitleCue]:
    clamped: list[SubtitleCue] = []
    for cue in cues:
        duration_ms = cue.end_ms - cue.start_ms
        chars = len(cue.text)
        if duration_ms <= 0 or chars == 0:
            continue
        cps = chars / (duration_ms / 1000.0)
        if cps > target_cps:
            adjusted = int(chars / target_cps * 1000)
            new_end = cue.start_ms + adjusted
            clamped.append(SubtitleCue(text=cue.text, start_ms=cue.start_ms, end_ms=new_end))
        else:
            clamped.append(cue)
    return clamped


def alignment_mse(predicted: list[SubtitleCue], gold: list[tuple[int, int]]) -> float:
    """Mean squared error (ms²) of cue boundaries vs gold."""

    n = min(len(predicted), len(gold))
    if n == 0:
        return float("inf")
    diffs: list[float] = []
    for cue, (gold_start, gold_end) in zip(predicted, gold[:n]):
        diffs.append((cue.start_ms - gold_start) ** 2)
        diffs.append((cue.end_ms - gold_end) ** 2)
    return sum(diffs) / len(diffs)