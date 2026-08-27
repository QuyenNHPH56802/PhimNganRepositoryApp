"""Prometheus metrics for API."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request, Response

metrics_router = APIRouter()

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    HTTP_REQUESTS = Counter(
        "translator_http_requests_total",
        "HTTP requests",
        labelnames=("method", "endpoint", "status"),
    )
    HTTP_DURATION = Histogram(
        "translator_http_request_duration_seconds",
        "HTTP request duration",
        labelnames=("method", "endpoint"),
        buckets=(0.005, 0.025, 0.1, 0.5, 1, 5, 10, 30),
    )
    PROVIDER_CALLS = Counter(
        "translator_provider_calls_total",
        "Total provider invocations",
        labelnames=("kind", "provider", "status"),
    )
    PROVIDER_DURATION = Histogram(
        "translator_provider_call_duration_seconds",
        "Provider call latency",
        labelnames=("kind", "provider"),
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
    )
    TTS_GENERATE_SECONDS = Histogram(
        "tts_generate_seconds",
        "TTS generation wall-clock seconds (excluding cache hits)",
        labelnames=("provider",),
        buckets=(0.05, 0.25, 1, 2, 5, 10, 30, 60, 120, 300),
    )
    TTS_AUDIO_SECONDS = Histogram(
        "tts_audio_seconds",
        "TTS audio duration generated (post-cache)",
        labelnames=("provider",),
        buckets=(0.5, 1, 5, 10, 30, 60, 120, 300),
    )
    ACTIVE_PROJECTS = Gauge(
        "translator_active_projects",
        "Currently active projects",
    )
    SHEDDER_STATE = Gauge(
        "translator_shedder_state",
        "Shedder state: 0=open, 1=soft, 2=hard",
    )

    @metrics_router.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


except ImportError:  # pragma: no cover - prometheus_client optional
    PROVIDER_CALLS = None  # type: ignore[assignment]
    PROVIDER_DURATION = None  # type: ignore[assignment]
    TTS_GENERATE_SECONDS = None  # type: ignore[assignment]
    TTS_AUDIO_SECONDS = None  # type: ignore[assignment]
    HTTP_REQUESTS = None  # type: ignore[assignment]
    HTTP_DURATION = None  # type: ignore[assignment]
    ACTIVE_PROJECTS = None  # type: ignore[assignment]
    SHEDDER_STATE = None  # type: ignore[assignment]

    @metrics_router.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=b"# prometheus_client not installed\n", media_type="text/plain")


async def observe_requests_middleware(request: Request, call_next):
    if HTTP_DURATION is None or HTTP_REQUESTS is None:
        return await call_next(request)
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    endpoint = request.url.path
    HTTP_DURATION.labels(method=request.method, endpoint=endpoint).observe(elapsed)
    HTTP_REQUESTS.labels(
        method=request.method, endpoint=endpoint, status=str(response.status_code)
    ).inc()
    return response


__all__ = [
    "ACTIVE_PROJECTS",
    "HTTP_DURATION",
    "HTTP_REQUESTS",
    "PROVIDER_CALLS",
    "PROVIDER_DURATION",
    "SHEDDER_STATE",
    "TTS_AUDIO_SECONDS",
    "TTS_GENERATE_SECONDS",
    "metrics_router",
]


def set_shedder_state(value: int) -> None:
    if SHEDDER_STATE is not None:
        SHEDDER_STATE.set(value)


def observe_provider_call(*, kind: str, provider: str, status: str, duration_seconds: float) -> None:
    if PROVIDER_CALLS is not None:
        PROVIDER_CALLS.labels(kind=kind, provider=provider, status=status).inc()
    if PROVIDER_DURATION is not None:
        PROVIDER_DURATION.labels(kind=kind, provider=provider).observe(duration_seconds)


def observe_tts_call(*, provider: str, generate_seconds: float, audio_seconds: float | None = None) -> None:
    """Record TTS generation timing on the API side.

    Mirrors the worker-side helper so dashboards aggregate the same
    metric name regardless of where the synthesis runs.
    """
    if TTS_GENERATE_SECONDS is not None:
        TTS_GENERATE_SECONDS.labels(provider=provider).observe(generate_seconds)
    if TTS_AUDIO_SECONDS is not None and audio_seconds is not None and audio_seconds > 0:
        TTS_AUDIO_SECONDS.labels(provider=provider).observe(audio_seconds)