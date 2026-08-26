"""Compare current benchmark run vs baseline.

Usage:
    python scripts/baseline_compare.py \
        --current reports/ci/summary.json \
        --baseline reports/baseline.json \
        --thresholds scripts/baseline_thresholds.yaml
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def _load_yaml(path: pathlib.Path) -> dict:
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=pathlib.Path, required=True)
    parser.add_argument("--baseline", type=pathlib.Path, required=True)
    parser.add_argument("--thresholds", type=pathlib.Path, default=pathlib.Path("scripts/baseline_thresholds.yaml"))
    args = parser.parse_args()

    current = json.loads(args.current.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    thresholds = _load_yaml(args.thresholds)

    failures: list[str] = []

    for provider, metrics in current.items():
        provider_thresholds = thresholds.get(provider, {})
        baseline_metrics = baseline.get("providers", {}).get(provider, {})
        for metric_name, value in metrics.items():
            if not isinstance(value, (int, float)):
                continue
            threshold = provider_thresholds.get(metric_name, {})
            min_value = threshold.get("min")
            max_value = threshold.get("max")
            regression = threshold.get("regression")
            if min_value is not None and value < min_value:
                failures.append(f"{provider}.{metric_name}={value} < min={min_value}")
            if max_value is not None and value > max_value:
                failures.append(f"{provider}.{metric_name}={value} > max={max_value}")
            baseline_value = baseline_metrics.get(metric_name)
            if baseline_value is not None and regression is not None:
                delta = value - baseline_value
                if regression < 0 and delta < regression:
                    failures.append(f"{provider}.{metric_name} regressed: {value} vs baseline {baseline_value} ({delta:.4f} < {regression})")
                if regression > 0 and delta > regression:
                    failures.append(f"{provider}.{metric_name} regressed: {value} vs baseline {baseline_value} ({delta:.4f} > {regression})")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("[baseline_compare] all providers within thresholds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())