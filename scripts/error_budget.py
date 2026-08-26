"""Error budget calculator.

Pulls SLO metrics from Prometheus and returns a burn-rate report.

Usage:
    python scripts/error_budget.py --prometheus http://prom:9090 --output reports/budget.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request


SLO_QUERIES = {
    "api_availability": {
        "objective": 0.995,
        "indicator": "translator_http_requests_total",
        "expression": "1 - (sum(rate(translator_http_requests_total{status=~'5..'}[30d])) / sum(rate(translator_http_requests_total[30d])))",
    },
    "workflow_p95_latency": {
        "objective_seconds": 300,
        "expression": "histogram_quantile(0.95, sum(rate(translator_http_request_duration_seconds_bucket{endpoint=~'/api/projects/.*/workflows'}[30d])) by (le))",
    },
    "queue_p99_depth": {
        "objective": 50,
        "expression": "histogram_quantile(0.99, sum(rate(translator_queue_depth[30d])) by (le))",
    },
}


def query(prometheus: str, expression: str) -> float | None:
    url = f"{prometheus.rstrip('/')}/api/v1/query?" + urllib.parse.urlencode({"query": expression})
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    results = body.get("data", {}).get("result", [])
    if not results:
        return None
    value = results[0].get("value", [None, None])[1]
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prometheus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report: dict[str, dict] = {}
    exceeded = 0
    for name, spec in SLO_QUERIES.items():
        measured = query(args.prometheus, spec["expression"])
        objective = spec.get("objective") or spec.get("objective_seconds")
        breach = False
        if measured is not None and objective is not None:
            if name == "api_availability":
                breach = measured < objective
            else:
                breach = measured > objective
        if breach:
            exceeded += 1
        report[name] = {
            "objective": objective,
            "measured": measured,
            "breach": breach,
            "budget_remaining_pct": None if measured is None else (
                round((measured / objective) * 100, 2) if name == "api_availability" else round((objective / measured) * 100, 2)
            ),
        }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump({"slos": report, "breached_count": exceeded}, handle, ensure_ascii=False, indent=2)
    if exceeded:
        print(f"[error_budget] {exceeded} SLO breach(es) — see {args.output}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())