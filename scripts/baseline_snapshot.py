"""Snapshot baseline from a benchmark run.

Usage:
    python scripts/baseline_snapshot.py \
        --reports reports/20240101T000000Z/benchmark.json \
        --out reports/baseline.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib


def aggregate(metric_buckets: list[dict]) -> dict[str, float | None]:
    aggregated: dict[str, float | None] = {}
    metric_keys = set()
    for bucket in metric_buckets:
        metric_keys.update(k for k in bucket if k != "id")
    for key in metric_keys:
        values = [bucket[key] for bucket in metric_buckets if isinstance(bucket.get(key), (int, float))]
        aggregated[key] = round(sum(values) / len(values), 4) if values else None
    return aggregated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", nargs="+", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    combined: dict[str, list[dict]] = {}
    for report_path in args.reports:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for provider, records in report["results"].items():
            combined.setdefault(provider, []).extend(records)

    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "providers": {
            provider: aggregate(records) for provider, records in combined.items()
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[baseline_snapshot] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())