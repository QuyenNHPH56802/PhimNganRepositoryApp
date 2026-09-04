"""User identity (resolved from session JWT or stub)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    email: str
    display_name: str | None = None
    provider: str = "stub"

    def as_audit_dict(self) -> dict[str, str]:
        return {"user_id": self.user_id, "email": self.email, "provider": self.provider}
