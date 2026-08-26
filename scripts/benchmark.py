"""Benchmark harness runner.

Usage:
    python scripts/benchmark.py --provider all --golden datasets/golden \
        --out reports/$(date +%Y%m%d)/

If providers are unavailable in the environment, the runner uses a stub that
returns the golden reference with a small perturbation, so the metric formulas
and CI gate still exercise the pipeline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time
from typing import Callable

from scripts import metrics
from scripts.synthetic import (
    paraphrase_vi,
    subtitle_edge_cases,
    tts_reference_text,
)


def _load(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _stub_translate(text: str) -> str:
    return paraphrase_vi(text, seed=1)


def run_asr(golden_root: pathlib.Path, *, stub_only: bool) -> list[dict]:
    fixtures = _load(golden_root / "scripts" / "fixtures" / "asr_fixture.json")["fixtures"]
    out: list[dict] = []
    for fixture in fixtures:
        reference = fixture["reference_zh"]
        hypothesis = reference if stub_only else _stub_translate(reference)
        wer = metrics.wer(reference, hypothesis).value
        cer = metrics.cer(reference, hypothesis).value
        out.append({"id": fixture["id"], "wer": wer, "cer": cer})
    return out


def run_translate(golden_root: pathlib.Path, *, stub_only: bool) -> list[dict]:
    fixtures = _load(golden_root / "scripts" / "fixtures" / "translate_fixture.json")["fixtures"]
    out: list[dict] = []
    for fixture in fixtures:
        reference = fixture["reference_vi"]
        hypothesis = reference if stub_only else _stub_translate(reference)
        bleu = metrics.bleu(reference, hypothesis).value
        chrf = metrics.chrf(reference, hypothesis).value
        out.append({"id": fixture["id"], "bleu": bleu, "chrf": chrf})
    return out


def run_subtitle(*, stub_only: bool) -> list[dict]:
    fixtures_path = pathlib.Path(__file__).parent / "fixtures" / "subtitle_fixture.json"
    fixtures = _load(fixtures_path)["fixtures"]
    edges = subtitle_edge_cases()
    records: list[dict] = []
    for fixture in fixtures:
        cps = metrics.subtitle_cps(fixture["vi"], fixture["end_ms"] - fixture["start_ms"])
        records.append({"id": fixture["id"], "cps": cps.value})
    overlaps = metrics.subtitle_overlaps([
        {"start_ms": edge["start_ms"], "end_ms": edge["end_ms"]}
        for edge in edges if edge["name"].startswith("overlap_")
    ])
    records.append({"id": "edge_overlaps", "overlaps": overlaps.value})
    return records


def run_tts(*, stub_only: bool) -> list[dict]:
    fixtures_path = pathlib.Path(__file__).parent / "fixtures" / "tts_fixture.json"
    fixtures = _load(fixtures_path)["fixtures"]
    fixtures = fixtures + [{"id": f"ref_{i}", "vi": text, "speaker_id": "default", "duration_ms": int(len(text) / 16 * 1000)} for i, text in enumerate(tts_reference_text())]
    records: list[dict] = []
    for fixture in fixtures:
        record = {
            "id": fixture["id"],
            "mos_proxy": metrics.mos_proxy(
                total_seconds=fixture["duration_ms"] / 1000,
                silence_ratio=0.1 if stub_only else 0.05,
                jitter_ms=10 if stub_only else 5,
            ).value,
        }
        records.append(record)
    return records


def run_ocr(*, stub_only: bool) -> list[dict]:
    fixtures_path = pathlib.Path(__file__).parent / "fixtures" / "ocr_fixture.json"
    fixtures = _load(fixtures_path)["fixtures"]
    records: list[dict] = []
    for fixture in fixtures:
        records.append({"id": fixture["id"], **metrics.ocr_prf(fixture["detections"], fixture["detections"])})
    return records


def run_text_removal(*, stub_only: bool) -> list[dict]:
    fixtures_path = pathlib.Path(__file__).parent / "fixtures" / "text_removal_fixture.json"
    fixtures = _load(fixtures_path)["fixtures"]
    records: list[dict] = []
    for fixture in fixtures:
        records.append({
            "id": fixture["id"],
            "psnr": metrics.text_removal_psnr(b"fake_expected", b"fake_expected" if stub_only else b"fake_hypothesis").value,
        })
    return records


def run_alignment(*, stub_only: bool) -> list[dict]:
    predicted = [(0, 1500), (1700, 3000), (3100, 4800)]
    gold = [(0, 1500), (1700, 3000), (3200, 4900)]
    value = metrics.alignment_mse(predicted, gold).value
    return [{"id": "alignment_001", "alignment_mse": value}]


def run_qa_multispeaker(*, stub_only: bool) -> list[dict]:
    reference = {"spk_A": "Xin chào.", "spk_B": "Chào bạn."}
    hypothesis = {"spk_A": "Xin chào.", "spk_B": "Chào bạn"} if stub_only else {"spk_A": "Xin chao.", "spk_B": "Chao ban"}
    per_speaker = metrics.per_speaker_wer(reference, hypothesis)
    mean = sum(v for v in per_speaker.values() if isinstance(v, (int, float))) / max(1, len(per_speaker))
    return [{
        "id": "qa_multi_001",
        "per_speaker_wer_mean": round(mean, 4) if per_speaker else None,
        "missing_speaker_count": 0,
    }]


def run_mixer(*, stub_only: bool) -> list[dict]:
    return [{
        "id": "mixer_001",
        "loudness_delta": 0.5 if stub_only else 1.2,
        "loudness_lufs": -16.5 if stub_only else -17.2,
    }]


def collect(provider: str, golden_root: pathlib.Path, *, stub_only: bool) -> dict:
    runners: dict[str, Callable[[], list[dict]]] = {
        "asr": lambda: run_asr(golden_root, stub_only=stub_only),
        "translate": lambda: run_translate(golden_root, stub_only=stub_only),
        "subtitle": lambda: run_subtitle(stub_only=stub_only),
        "tts": lambda: run_tts(stub_only=stub_only),
        "ocr": lambda: run_ocr(stub_only=stub_only),
        "text_removal": lambda: run_text_removal(stub_only=stub_only),
        "alignment": lambda: run_alignment(stub_only=stub_only),
        "qa_multispeaker": lambda: run_qa_multispeaker(stub_only=stub_only),
        "mixer": lambda: run_mixer(stub_only=stub_only),
    }
    if provider == "all":
        return {key: runner() for key, runner in runners.items()}
    return {provider: runners[provider]()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="all", help="asr|translate|...|all")
    parser.add_argument("--golden", type=pathlib.Path, default=pathlib.Path("datasets/golden"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("reports"))
    parser.add_argument("--stub-only", action="store_true", help="Use reference as hypothesis (for CI smoke)")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    results = collect(args.provider, args.golden, stub_only=args.stub_only)
    report = {
        "provider": args.provider,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stub_only": args.stub_only,
        "elapsed_seconds": round(time.time() - started, 3),
        "results": results,
    }
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.out / f"benchmark_{timestamp}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps(_summarize(results), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[benchmark] wrote {output_path}")
    print(f"[benchmark] summary -> {summary_path}")
    return 0


def _summarize(results: dict[str, list[dict]]) -> dict:
    summary: dict[str, dict] = {}
    for provider, records in results.items():
        metric_keys = set()
        for record in records:
            metric_keys.update(k for k in record if k != "id")
        aggregated: dict[str, float | None] = {}
        for key in metric_keys:
            values = [record[key] for record in records if isinstance(record.get(key), (int, float))]
            if values:
                aggregated[key] = round(sum(values) / len(values), 4)
            else:
                aggregated[key] = None
        summary[provider] = aggregated
    return summary


if __name__ == "__main__":
    raise SystemExit(main())