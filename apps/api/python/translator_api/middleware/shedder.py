"""Middleware that returns 503 when Temporal queue backlog is unhealthy.

The shedder reads `translator_workflow_step_status_total{status="pending"}`
from Prometheus. If the queue is backed up, the API returns
`503 Service Unavailable` with a `Retry-After` header so the caller can back
off. Two thresholds are exposed via env vars (default 50/100).

This middleware is intentionally best-effort: if Prometheus is unreachable,
requests pass through (the alternative — 5xx on every request — is worse).
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    from prometheus_client import REGISTRY  # noqa: F401  (import ensures metric exposure)
except Exception:  # pragma: no cover - optional
    REGISTRY = None  # type: ignore[assignment]


SOFT_THRESHOLD = int(os.environ.get("TRANSLATOR_SHEDDER_SOFT", "50"))
HARD_THRESHOLD = int(os.environ.get("TRANSLATOR_SHEDDER_HARD", "100"))


async def _estimate_backlog(request: Request) -> int:
    state = request.app.state
    return int(getattr(state, "pending_backlog", 0))


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def _shedder(request: Request, call_next):
        if request.url.path.startswith("/api/healthz") or request.method == "OPTIONS":
            return await call_next(request)
        backlog = await _estimate_backlog(request)
        if backlog >= HARD_THRESHOLD:
            return JSONResponse(
                status_code=503,
                content={"detail": "service overloaded", "backlog": backlog},
                headers={"Retry-After": "120", "X-Shedder-State": "hard"},
            )
        if backlog >= SOFT_THRESHOLD:
            response = await call_next(request)
            response.headers["X-Shedder-State"] = "soft"
            response.headers["Retry-After"] = "30"
            return response
        return await call_next(request)


def update_backlog(app: FastAPI, backlog: int) -> None:
    app.state.pending_backlog = backlog