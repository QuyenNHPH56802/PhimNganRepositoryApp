"""Worker Prometheus metrics."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import time

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        multiprocess,
    )

    REGISTRY = CollectorRegistry()

    ACTIVITY_CALLS = Counter(
        "translator_activity_calls_total",
        "Activity invocations",
        labelnames=("name", "status"),
        registry=REGISTRY,
    )
    ACTIVITY_DURATION = Histogram(
        "translator_activity_duration_seconds",
        "Activity duration",
        labelnames=("name",),
        buckets=(0.5, 1, 5, 10, 30, 60, 120, 600),
        registry=REGISTRY,
    )
    QUEUE_DEPTH = Gauge(
        "translator_queue_depth",
        "Workflows pending in queue",
        labelnames=("task_queue",),
        registry=REGISTRY,
    )
    CACHE_HIT = Counter(
        "translator_cache_hit_total",
        "ArtifactCache hit",
        labelnames=("kind",),
        registry=REGISTRY,
    )
    CACHE_MISS = Counter(
        "translator_cache_miss_total",
        "ArtifactCache miss",
        labelnames=("kind",),
        registry=REGISTRY,
    )
    GPU_MEMORY_USED = Gauge(
        "translator_gpu_memory_used_bytes",
        "GPU memory used",
        labelnames=("gpu_index",),
        registry=REGISTRY,
    )
    GPU_MEMORY_TOTAL = Gauge(
        "translator_gpu_memory_total_bytes",
        "GPU memory total",
        labelnames=("gpu_index",),
        registry=REGISTRY,
    )
    GPU_UTILIZATION = Gauge(
        "translator_gpu_utilization",
        "GPU utilization (0-100)",
        labelnames=("gpu_index",),
        registry=REGISTRY,
    )
    PROBE_SUCCESS = Gauge(
        "translator_probe_success",
        "Synthetic probe result: 1=ok, 0=failed",
        registry=REGISTRY,
    )

    def render() -> bytes:
        return generate_latest(REGISTRY)

    CONTENT_TYPE = CONTENT_TYPE_LATEST

except ImportError:  # pragma: no cover - prometheus_client optional
    REGISTRY = None  # type: ignore[assignment]

    class _Stub:
        def labels(self, **_):
            return self

        def inc(self, *_):
            return None

        def observe(self, *_):
            return None

        def set(self, *_):
            return None

    def _stub():
        return _Stub()

    ACTIVITY_CALLS = _stub()  # type: ignore[assignment]
    ACTIVITY_DURATION = _stub()
    QUEUE_DEPTH = _stub()
    CACHE_HIT = _stub()
    CACHE_MISS = _stub()
    GPU_MEMORY_USED = _stub()
    GPU_MEMORY_TOTAL = _stub()
    GPU_UTILIZATION = _stub()
    PROBE_SUCCESS = _stub()

    def render() -> bytes:
        return b"# prometheus_client not installed\n"

    CONTENT_TYPE = "text/plain"


__all__ = [
    "ACTIVITY_CALLS",
    "ACTIVITY_DURATION",
    "CACHE_HIT",
    "CACHE_MISS",
    "CONTENT_TYPE",
    "GPU_MEMORY_TOTAL",
    "GPU_MEMORY_USED",
    "GPU_UTILIZATION",
    "PROBE_SUCCESS",
    "QUEUE_DEPTH",
    "REGISTRY",
    "render",
]


def observe_activity(name: str, *, status: str, duration_seconds: float) -> None:
    ACTIVITY_CALLS.labels(name=name, status=status).inc()
    ACTIVITY_DURATION.labels(name=name).observe(duration_seconds)


def record_cache_lookup(*, kind: str, hit: bool) -> None:
    if hit:
        CACHE_HIT.labels(kind=kind).inc()
    else:
        CACHE_MISS.labels(kind=kind).inc()


async def poll_gpu_metrics(interval_seconds: float = 15.0) -> None:
    """Background task: poll `nvidia-smi` every `interval_seconds`."""

    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return
    while True:
        try:
            await asyncio.to_thread(_poll_once, nvidia_smi)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)


def _poll_once(nvidia_smi: str) -> None:
    completed = subprocess.run(
        [nvidia_smi, "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return
    for line in completed.stdout.splitlines():
        parts = [segment.strip() for segment in line.split(",")]
        if len(parts) != 4:
            continue
        index, used_mib, total_mib, util = parts
        GPU_MEMORY_USED.labels(gpu_index=index).set(float(used_mib) * 1024 * 1024)
        GPU_MEMORY_TOTAL.labels(gpu_index=index).set(float(total_mib) * 1024 * 1024)
        try:
            GPU_UTILIZATION.labels(gpu_index=index).set(float(util))
        except ValueError:
            continue


async def report_probe(success: bool) -> None:
    PROBE_SUCCESS.set(1.0 if success else 0.0)