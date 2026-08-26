"""Structured logging (delegates to observability.tracing.configure_logging)."""

from __future__ import annotations

from translator_api.observability.tracing import (
    JsonFormatter,
    configure_logging,
    parse_traceparent,
    mint_traceparent,
)

__all__ = ["JsonFormatter", "configure_logging", "mint_traceparent", "parse_traceparent"]