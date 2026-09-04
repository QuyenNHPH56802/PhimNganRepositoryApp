"""Error reporter — Sentry-compatible payload.

Phase 9 ships a minimal reporter that captures exceptions and flushes to:
- STDOUT (default, dev/test)
- HTTP_POST (`TRANSLATOR_SINK_URL`)
- NULL (test)

Payload shape follows the public Sentry envelope format so a future
Sentry-compatible backend (Self-Hosted Sentry / GlitchTip) can ingest
without code changes.
"""

from __future__ import annotations

import json
import os
import threading
import traceback
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Sink(Enum):
    STDOUT = "stdout"
    HTTP_POST = "http_post"
    NULL = "null"


@dataclass
class ErrorEvent:
    exception_type: str
    message: str
    stacktrace: str
    timestamp: str
    tags: dict[str, str] = field(default_factory=dict)
    breadcrumbs: list[dict[str, Any]] = field(default_factory=list)
    release: str = os.environ.get("TRANSLATOR_RELEASE", "dev")
    environment: str = os.environ.get("TRANSLATOR_ENV", "development")

    def to_envelope(self) -> dict[str, Any]:
        return {
            "platform": "python",
            "level": "error",
            "exception": {
                "type": self.exception_type,
                "value": self.message,
                "stacktrace": self.stacktrace,
            },
            "tags": self.tags,
            "breadcrumbs": {"values": self.breadcrumbs},
            "timestamp": self.timestamp,
            "release": self.release,
            "environment": self.environment,
        }


class ErrorReporter:
    def __init__(self, *, sink: Sink | None = None, sink_url: str | None = None) -> None:
        env_sink = os.environ.get("TRANSLATOR_SINK", "stdout").lower()
        self._sink = sink or Sink(env_sink)
        self._sink_url = sink_url or os.environ.get("TRANSLATOR_SINK_URL")
        self._breadcrumbs: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._flushers: dict[Sink, Callable[[ErrorEvent], None]] = {
            Sink.STDOUT: self._flush_stdout,
            Sink.HTTP_POST: self._flush_http,
            Sink.NULL: lambda _event: None,
        }

    def add_breadcrumb(self, *, message: str, category: str = "default", data: dict | None = None) -> None:
        with self._lock:
            self._breadcrumbs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "category": category,
                "message": message,
                "data": data or {},
            })

    def capture_exception(self, exc: BaseException, *, tags: dict[str, str] | None = None) -> ErrorEvent:
        event = ErrorEvent(
            exception_type=type(exc).__name__,
            message=str(exc),
            stacktrace=traceback.format_exc(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tags=tags or {},
            breadcrumbs=list(self._breadcrumbs),
        )
        flusher = self._flushers.get(self._sink, self._flush_stdout)
        try:
            flusher(event)
        except Exception:  # never raise from reporter
            pass
        return event

    def _flush_stdout(self, event: ErrorEvent) -> None:
        print(json.dumps(event.to_envelope(), ensure_ascii=False), flush=True)

    def _flush_http(self, event: ErrorEvent) -> None:
        if not self._sink_url:
            return
        payload = json.dumps(event.to_envelope(), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(self._sink_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(request, timeout=5).read()


_reporter: ErrorReporter | None = None


def get_reporter() -> ErrorReporter:
    global _reporter
    if _reporter is None:
        _reporter = ErrorReporter()
    return _reporter


def install_fastapi(app) -> None:
    """Attach an exception capture middleware."""

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class _CaptureMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            reporter = get_reporter()
            reporter.add_breadcrumb(message=f"{request.method} {request.url.path}", category="http")
            try:
                return await call_next(request)
            except Exception as exc:
                reporter.capture_exception(exc, tags={"endpoint": request.url.path, "method": request.method})
                raise

    app.add_middleware(_CaptureMiddleware)
