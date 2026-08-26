"""Provider-side helpers for activity/registry reuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from translator_api.providers.base import Provider
from translator_shared.providers import FallbackPolicy


@dataclass(frozen=True)
class FallbackChain:
    """A list of providers tried in order; the first successful result wins."""

    primary: Provider
    fallbacks: tuple[Provider, ...]
    policy: FallbackPolicy = FallbackPolicy.PREFER_ALT

    def candidates(self) -> list[Provider]:
        return [self.primary, *self.fallbacks]


def merge_config(defaults: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(defaults)
    if override:
        merged.update(override)
    return merged