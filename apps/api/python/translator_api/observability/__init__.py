"""Observability package (tracing, metrics, structured logging)."""

from translator_api.observability.error_reporter import get_reporter, install_fastapi
from translator_api.observability.logging import configure_logging
from translator_api.observability.metrics import (
    PROVIDER_CALLS,
    PROVIDER_DURATION,
    observe_provider_call,
    observe_requests_middleware,
    set_shedder_state,
    metrics_router,
)
from translator_api.observability.tracing import (
    TRACE_HEADER,
    mint_traceparent,
    parse_traceparent,
    setup_telemetry,
    trace_id_var,
)

__all__ = [
    "PROVIDER_CALLS",
    "PROVIDER_DURATION",
    "TRACE_HEADER",
    "configure_logging",
    "get_reporter",
    "install_fastapi",
    "metrics_router",
    "mint_traceparent",
    "observe_provider_call",
    "observe_requests_middleware",
    "parse_traceparent",
    "set_shedder_state",
    "setup_telemetry",
    "trace_id_var",
]