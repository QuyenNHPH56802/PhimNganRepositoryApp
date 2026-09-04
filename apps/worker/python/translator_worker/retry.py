"""Retry policy tables mirroring docs/workflow.md."""

from __future__ import annotations

from datetime import timedelta

from temporalio.common import RetryPolicy

DEFAULT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    non_retryable_error_types=["CapabilityUnsupported", "ConsentMissing"],
)

LONG_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=2,
)

SHORT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=8),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

QA_NO_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=1,
)
