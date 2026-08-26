"""Rate limiting + circuit breaker utilities."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Generic, TypeVar

from translator_api.providers.base import (
    CapabilityUnsupported,
    ConsentMissing,
    ProviderError,
)

T = TypeVar("T")


@dataclass
class CircuitBreaker:
    """Async-safe circuit breaker for provider HTTP calls."""

    failure_threshold: int = 5
    recovery_seconds: float = 30.0
    _failures: int = 0
    _opened_at: float | None = None

    async def execute(self, call: Callable[[], Awaitable[T]]) -> T:
        self._maybe_recover()
        if self.is_open():
            raise ProviderError("circuit-open", "circuit breaker is open", retryable=False)
        try:
            result = await call()
        except (CapabilityUnsupported, ConsentMissing):
            raise
        except Exception:
            self._failures += 1
            self._opened_at = time.time()
            raise
        self._failures = 0
        self._opened_at = None
        return result

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        return (time.time() - self._opened_at) < self.recovery_seconds

    def _maybe_recover(self) -> None:
        if self._opened_at is None:
            return
        if (time.time() - self._opened_at) >= self.recovery_seconds:
            self._opened_at = None
            self._failures = 0


@dataclass
class TokenBucket:
    capacity: float
    refill_rate_per_second: float
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.time()

    def acquire(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        now = time.time()
        elapsed = max(0.0, now - self._last_refill)
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate_per_second)
        self._last_refill = now


class SlidingWindowRedis:
    """Sliding-window counter backed by Redis.

    Phase 4 ships the protocol without locking on the redis import; if
    `redis.asyncio` is missing, callers can pass a stub or fall back to the
    in-process TokenBucket above.
    """

    def __init__(self, *, client, key_prefix: str, window_seconds: int, limit: int) -> None:
        self._client = client
        self._prefix = key_prefix
        self._window = window_seconds
        self._limit = limit

    async def hit(self, *, identity: str) -> tuple[bool, int]:
        key = f"{self._prefix}:{identity}"
        try:
            count = await self._client.incr(key)
            if count == 1:
                await self._client.expire(key, self._window)
            return (int(count) <= self._limit, max(0, self._limit - int(count)))
        except Exception:
            return (True, self._limit)


async def run_with_breaker(breaker: CircuitBreaker, call: Callable[[], Awaitable[T]]) -> T:
    return await breaker.execute(call)