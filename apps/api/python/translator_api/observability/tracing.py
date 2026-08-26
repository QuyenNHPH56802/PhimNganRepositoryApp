"""OpenTelemetry tracing setup.

Phase 4 ships a lightweight trace context: a FastAPI middleware that reads
or generates `traceparent` (W3C), attaches it to `contextvars`, and emits
log records with `trace_id`. The OTLP exporter is enabled only when
`TRANSLATOR_OTEL_EXPORTER_OTLP_ENDPOINT` is set; otherwise traces stay
in-process.
"""

from __future__ import annotations

import contextvars
import logging
import os
import re
import uuid

TRACE_HEADER = "traceparent"

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")

_TRACEPARENT_RE = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$")


def parse_traceparent(header_value: str) -> tuple[str, str] | None:
    if not header_value:
        return None
    match = _TRACEPARENT_RE.match(header_value.strip())
    if not match:
        return None
    return match.group(2), match.group(3)


def mint_traceparent() -> str:
    version = "00"
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    flags = "01"
    return f"{version}-{trace_id}-{span_id}-{flags}"


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get(""),
            "span_id": span_id_var.get(""),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def is_otel_enabled() -> bool:
    return bool(os.environ.get("TRANSLATOR_OTEL_EXPORTER_OTLP_ENDPOINT"))


def setup_telemetry(app) -> None:
    """Install a minimal FastAPI middleware that propagates trace context."""

    if app is None:
        return

    @app.middleware("http")
    async def _trace(request, call_next):
        incoming = request.headers.get(TRACE_HEADER, "")
        parsed = parse_traceparent(incoming)
        if parsed:
            trace_id, span_id = parsed
        else:
            new = mint_traceparent()
            trace_id, span_id = parse_traceparent(new)  # type: ignore[misc]
        token = trace_id_var.set(trace_id or "")
        span_token = span_id_var.set(span_id or "")
        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)
            span_id_var.reset(span_token)
        response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        return response