"""Provider abstraction."""

from __future__ import annotations

from translator_api.providers.base import (
    CapabilityUnsupported,
    ConsentMissing,
    Provider,
    ProviderCapabilities,
    ProviderContext,
    ProviderError,
    ProviderRegistry,
)

__all__ = [
    "CapabilityUnsupported",
    "ConsentMissing",
    "Provider",
    "ProviderCapabilities",
    "ProviderContext",
    "ProviderError",
    "ProviderRegistry",
]