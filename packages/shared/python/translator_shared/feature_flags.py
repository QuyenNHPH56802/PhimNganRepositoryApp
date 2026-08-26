"""In-process feature flag registry.

Phase 10 ships a lightweight registry with ENV + file overrides. The
goal is to ship features safely behind flags without depending on an
external system like LaunchDarkly.

Override order:
    ENV > JSON file > default
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class FlagState(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"
    GA = "ga"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class FlagSpec:
    name: str
    state: FlagState
    default: bool = False
    rollout_percent: int = 0
    description: str = ""
    deprecated_at: dt.datetime | None = None
    removal_at: dt.datetime | None = None


@dataclass
class FlagAudit:
    name: str
    enabled: bool
    source: str
    at: dt.datetime
    subject: str | None = None


class FeatureFlagRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, FlagSpec] = {}
        self._env_overrides: dict[str, bool] = {}
        self._file_overrides: dict[str, bool] = {}
        self._audits: list[FlagAudit] = []
        self._lock = threading.Lock()

    def register(self, spec: FlagSpec) -> None:
        with self._lock:
            self._specs[spec.name] = spec

    def override_env(self, name: str, value: bool | None) -> None:
        with self._lock:
            if value is None:
                self._env_overrides.pop(name, None)
            else:
                self._env_overrides[name] = value

    def override_file(self, path: str) -> None:
        try:
            payload = json.loads(open(path, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            return
        with self._lock:
            self._file_overrides.update(payload)

    def _resolve(self, name: str) -> tuple[bool, str]:
        if name not in self._specs:
            return False, "missing-spec"
        env_name = "FLAG_" + name.upper().replace(".", "_").replace("-", "_")
        env_value = os.environ.get(env_name)
        if env_value is not None:
            return _truthy(env_value), "env"
        if name in self._env_overrides:
            return self._env_overrides[name], "env_explicit"
        if name in self._file_overrides:
            return self._file_overrides[name], "file"
        return self._specs[name].default, "default"

    def is_enabled(self, name: str, *, subject: str | None = None) -> bool:
        enabled, source = self._resolve(name)
        spec = self._specs.get(name)
        if enabled and spec and spec.rollout_percent < 100 and subject:
            bucket = int(hashlib.sha1(subject.encode("utf-8")).hexdigest(), 16) % 100
            enabled = bucket < spec.rollout_percent
            if not enabled:
                source = f"{source}+rollout-skipped"
        with self._lock:
            self._audits.append(FlagAudit(name=name, enabled=enabled, source=source, at=dt.datetime.utcnow(), subject=subject))
        return enabled

    def audit(self) -> list[dict]:
        with self._lock:
            return [
                {"name": a.name, "enabled": a.enabled, "source": a.source, "at": a.at.isoformat(), "subject": a.subject}
                for a in self._audits
            ]

    def describe(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "name": spec.name,
                    "state": spec.state.value,
                    "default": spec.default,
                    "rollout_percent": spec.rollout_percent,
                    "deprecated_at": spec.deprecated_at.isoformat() if spec.deprecated_at else None,
                    "removal_at": spec.removal_at.isoformat() if spec.removal_at else None,
                }
                for spec in self._specs.values()
            ]


def _truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


_registry = FeatureFlagRegistry()


def get_registry() -> FeatureFlagRegistry:
    return _registry


def register_default_flags(registry: FeatureFlagRegistry | None = None) -> None:
    reg = registry or _registry
    reg.register(FlagSpec(name="workflow.subtitle_alignment_v2", state=FlagState.BETA, default=False, rollout_percent=25, description="Phase 7 alignment v2"))
    reg.register(FlagSpec(name="pipeline.voice_clone", state=FlagState.ALPHA, default=False, description="Phase 7 voice cloning pipeline"))
    reg.register(FlagSpec(name="admin.dataset_manager", state=FlagState.GA, default=True, description="Phase 8 dataset manager"))


def is_enabled(name: str, *, subject: str | None = None) -> bool:
    return _registry.is_enabled(name, subject=subject)


def enabled_or(fn: Callable[[], object]) -> Callable[[], object]:
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        if not is_enabled(fn.__name__):
            return None
        return fn(*args, **kwargs)

    return wrapper