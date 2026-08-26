"""Metric implementations for benchmark harness.

Each metric is a pure function. They tolerate missing optional dependencies
(`jiwer`, `sacrebleu`, `numpy`) by returning `None` and emitting a warning
so the CI does not fail purely on missing packages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: float | None
    extra: dict[str, float | int | None] | None = None


def _try_import(name: str):
    try:
        return __import__(name)
    except Exception:  # pragma: no cover - import is best-effort
        return None


def wer(reference: str, hypothesis: str) -> MetricValue:
    jiwer = _try_import("jiwer")
    if jiwer is None:
        return MetricValue(name="wer", value=None, extra={"hint": "jiwer not installed"})
    score = jiwer.wer(reference, hypothesis)
    return MetricValue(name="wer", value=float(score))


def cer(reference: str, hypothesis: str) -> MetricValue:
    jiwer = _try_import("jiwer")
    if jiwer is None:
        return MetricValue(name="cer", value=None, extra={"hint": "jiwer not installed"})
    transformations = jiwer.Compose([jiwer.ToLower(), jiwer.RemovePunctuation(), jiwer.Strip()])
    score = jiwer.process_words([reference], [hypothesis], reference_transform=transformations, hypothesis_transform=transformations)
    return MetricValue(name="cer", value=float(score.cer), extra={"hits": score.hits, "substitutions": score.substitutions, "deletions": score.deletions, "insertions": score.insertions})


def bleu(reference: str, hypothesis: str) -> MetricValue:
    sacrebleu = _try_import("sacrebleu")
    if sacrebleu is None:
        return MetricValue(name="bleu", value=None, extra={"hint": "sacrebleu not installed"})
    score = sacrebleu.sentence_bleu(hypothesis, [reference]).score
    return MetricValue(name="bleu", value=float(score))


def chrf(reference: str, hypothesis: str) -> MetricValue:
    sacrebleu = _try_import("sacrebleu")
    if sacrebleu is None:
        return MetricValue(name="chrf", value=None, extra={"hint": "sacrebleu not installed"})
    score = sacrebleu.sentence_chrf(hypothesis, [reference]).score
    return MetricValue(name="chrf", value=float(score))


def subtitle_cps(text: str, duration_ms: int) -> MetricValue:
    seconds = max(1e-6, duration_ms / 1000.0)
    cps = len(text) / seconds
    return MetricValue(name="cps", value=float(cps))


def subtitle_overlaps(subs: Iterable[dict[str, int]]) -> MetricValue:
    sorted_subs = sorted(subs, key=lambda s: s["start_ms"])
    overlaps = 0
    for prev, curr in zip(sorted_subs, sorted_subs[1:]):
        if curr["start_ms"] < prev["end_ms"]:
            overlaps += 1
    return MetricValue(name="overlaps", value=float(overlaps))


def mos_proxy(*, total_seconds: float, silence_ratio: float, jitter_ms: float) -> MetricValue:
    """Heuristic MOS proxy in [1, 5].

    Based on silence ratio (high silence -> bad), jitter (high jitter -> bad),
    and a duration sanity check.
    """

    silence_score = max(0.0, 1.0 - silence_ratio) * 2.5
    jitter_score = max(0.0, 1.0 - min(1.0, jitter_ms / 50.0)) * 1.5
    duration_score = 1.0 if 0.5 <= total_seconds <= 60.0 else 0.5
    return MetricValue(name="mos_proxy", value=round(silence_score + jitter_score + duration_score, 3))


def ocr_prf(reference: list[dict[str, object]], hypothesis: list[dict[str, object]], *, iou_threshold: float = 0.5) -> dict[str, float | int]:
    """Compute precision/recall/F1 over bbox IoU on text-match."

    A detection matches if text equality holds and IoU >= threshold.
    """

    matched = 0
    used = set()
    for hyp in hypothesis:
        hyp_bbox = hyp.get("bbox") or []
        for idx, ref in enumerate(reference):
            if idx in used:
                continue
            if ref.get("text") != hyp.get("text"):
                continue
            ref_bbox = ref.get("bbox") or []
            if _bbox_iou(_normalize(hyp_bbox), _normalize(ref_bbox)) >= iou_threshold:
                matched += 1
                used.add(idx)
                break
    precision = matched / max(1, len(hypothesis))
    recall = matched / max(1, len(reference))
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1, "matched": matched}


def text_removal_psnr(reference: bytes, hypothesis: bytes) -> MetricValue:
    """Cheap proxy: compare byte length + identical flag. Real PSNR requires PIL/numpy."""

    np = _try_import("numpy")
    if np is None:
        equal = reference == hypothesis
        return MetricValue(name="psnr_proxy", value=40.0 if equal else None, extra={"equal_bytes": equal})
    a = np.frombuffer(reference, dtype=np.uint8).astype("float32")
    b = np.frombuffer(hypothesis, dtype=np.uint8).astype("float32")
    if a.shape != b.shape:
        return MetricValue(name="psnr", value=None, extra={"hint": "shape mismatch"})
    mse = float(((a - b) ** 2).mean())
    if mse <= 0:
        return MetricValue(name="psnr", value=math.inf)
    return MetricValue(name="psnr", value=10.0 * math.log10(255.0 * 255.0 / mse))


def alignment_mse(predicted: list[tuple[int, int]], gold: list[tuple[int, int]]) -> MetricValue:
    """Mean squared error (ms²) between two lists of (start_ms, end_ms) cues."""

    if not predicted or not gold:
        return MetricValue(name="alignment_mse", value=None, extra={"hint": "empty cue lists"})
    n = min(len(predicted), len(gold))
    diffs: list[float] = []
    for (pred_start, pred_end), (gold_start, gold_end) in zip(predicted[:n], gold[:n]):
        diffs.append((pred_start - gold_start) ** 2)
        diffs.append((pred_end - gold_end) ** 2)
    return MetricValue(name="alignment_mse", value=sum(diffs) / len(diffs))


def per_speaker_wer(reference: dict[str, str], hypothesis: dict[str, str]) -> dict[str, float | None]:
    jiwer = _try_import("jiwer")
    result: dict[str, float | None] = {}
    speakers = set(reference.keys()) | set(hypothesis.keys())
    for speaker in sorted(speakers):
        ref = reference.get(speaker, "")
        hyp = hypothesis.get(speaker, "")
        if jiwer is None:
            result[speaker] = None
            continue
        result[speaker] = float(jiwer.wer(ref, hyp)) if ref.strip() else 0.0
    return result


def loudness_lufs(audio_path: str) -> MetricValue:
    """Return integrated loudness (LUFS) via `ffmpeg -af ebur128`. Returns None if missing."""

    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return MetricValue(name="loudness_lufs", value=None, extra={"hint": "ffmpeg not installed"})
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", audio_path, "-af", "ebur128", "-f", "null", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    for line in completed.stderr.splitlines():
        if "Integrated loudness" in line:
            tail = line.split(":")[-1].strip().split()
            try:
                return MetricValue(name="loudness_lufs", value=float(tail[0]))
            except (ValueError, IndexError):
                continue
    return MetricValue(name="loudness_lufs", value=None, extra={"hint": "ebur128 unavailable"})


def loudness_delta_metric(measured: float | None, target: float = -16.0) -> MetricValue:
    if measured is None:
        return MetricValue(name="loudness_delta", value=None, extra={"hint": "no measurement"})
    return MetricValue(name="loudness_delta", value=abs(measured - target))


def _normalize(bbox: list[int]) -> tuple[int, int, int, int]:
    xs = bbox[0::2]
    ys = bbox[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def _bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union else 0.0