"""Provider base classes and shared error types.

Every concrete provider returns one of:
- a Pydantic response model (success)
- CapabilityUnsupported (model missing, GPU missing, language unsupported)
- ConsentMissing (provider requires accepting user agreement, e.g. pyannote)
- ProviderError (generic failure; may be retryable)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session as SA_Session

from translator_api.storage_pkg.base import Storage
from translator_shared.providers import ArtifactSignature

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class ProviderError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class CapabilityUnsupported(ProviderError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, retryable=False)


class ConsentMissing(ProviderError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, retryable=False)


@dataclass(frozen=True)
class ProviderCapabilities:
    requires_gpu: bool = False
    requires_consent: bool = False
    is_local: bool = True
    supports_languages: tuple[str, ...] = ()


@dataclass
class ProviderContext:
    project_id: str | UUID
    asset_id: str | UUID | None = None
    db_session: SA_Session | None = None
    storage: Storage | None = None
    cache_dir: str = "./.provider-cache"
    voice_consent: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Provider(Generic[InputT, OutputT]):
    id: str = ""
    capabilities: ProviderCapabilities = ProviderCapabilities()

    async def run(self, payload: InputT, *, ctx: ProviderContext) -> OutputT:  # pragma: no cover - abstract
        raise NotImplementedError

    def fingerprint(self, payload: InputT) -> ArtifactSignature:
        return ArtifactSignature(
            input_hash="pending",
            model_id=self.id,
            model_version="0.0.0",
            provider_build="phase2",
            config_hash="pending",
        )


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], Provider] = {}

    def register(self, kind: str, provider: Provider) -> None:
        if not provider.id:
            raise ValueError(f"provider for {kind} missing id")
        self._providers[(kind, provider.id)] = provider

    def get(self, kind: str, provider_id: str) -> Provider:
        provider = self._providers.get((kind, provider_id))
        if provider is None:
            raise CapabilityUnsupported(f"{kind}-{provider_id}-not-registered", f"{kind}/{provider_id} not registered")
        return provider

    def has(self, kind: str, provider_id: str) -> bool:
        return (kind, provider_id) in self._providers

    def list(self, kind: str) -> list[str]:
        return [pid for (k, pid) in self._providers if k == kind]

    def list_providers(self, kind: str) -> list[Provider]:
        return [p for (k, _), p in self._providers.items() if k == kind]


_default_registry = ProviderRegistry()


def get_default_registry() -> ProviderRegistry:
    return _default_registry
