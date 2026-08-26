"""Scale test: trigger N projects in parallel and record latency.

Phase 6 ships this as a CLI smoke-test. It POSTs to the API
(`/projects`) and then triggers a workflow (`/projects/{id}/workflows`)
simulating real traffic. It DOES NOT depend on ML providers — only on
the orchestration + queue + cache layer.

Usage:
    python scripts/scale_test.py --projects 10 \
        --api http://localhost:8000/api \
        --out reports/scale/$(date +%Y%m%d)
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import pathlib
import statistics
import sys
import time

import httpx


async def _create_project(client: httpx.AsyncClient, api: str, token: str, idx: int) -> str:
    response = await client.post(
        f"{api}/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": f"scale_test_{idx:04d}", "source_language": "zh", "target_language": "vi"},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    return str(body["id"])


async def _trigger_workflow(client: httpx.AsyncClient, api: str, token: str, project_id: str) -> float:
    start = time.perf_counter()
    response = await client.post(
        f"{api}/projects/{project_id}/workflows",
        headers={"Authorization": f"Bearer {token}"},
        json={"quality_mode": "ONLY_SUBTITLE", "config": {}},
        timeout=60,
    )
    response.raise_for_status()
    return time.perf_counter() - start


async def run(api: str, token: str, n: int, concurrency: int) -> dict:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        async def task(idx: int) -> dict:
            async with sem:
                project_id = await _create_project(client, api, token, idx)
                latency = await _trigger_workflow(client, api, token, project_id)
                return {"project_id": project_id, "latency_seconds": latency}

        results = await asyncio.gather(*[task(i) for i in range(n)])
    latencies = sorted(r["latency_seconds"] for r in results)
    return {
        "project_count": n,
        "concurrency": concurrency,
        "latencies": latencies,
        "p50": _percentile(latencies, 50),
        "p95": _percentile(latencies, 95),
        "p99": _percentile(latencies, 99),
        "mean": statistics.mean(latencies) if latencies else 0.0,
    }


def _percentile(sorted_values: list[float], pct: int) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * pct / 100
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000/api")
    parser.add_argument("--token", default="")
    parser.add_argument("--projects", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("reports/scale"))
    args = parser.parse_args()

    if not args.token:
        print("[scale_test] missing --token; supply via env TRANSLATOR_TEST_TOKEN", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary = asyncio.run(run(args.api, args.token, args.projects, args.concurrency))
    summary["elapsed_seconds"] = round(time.time() - started, 3)
    summary["timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat()

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.out / f"scale_{timestamp}.json"
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps({k: summary[k] for k in ("project_count", "concurrency", "p50", "p95", "p99", "mean", "elapsed_seconds")}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[scale_test] wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())