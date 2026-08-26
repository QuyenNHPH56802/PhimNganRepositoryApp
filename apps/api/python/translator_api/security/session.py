"""Session JWT (HS256).

Phase 4 uses HS256 with a shared secret from TRANSLATOR_SESSION_SECRET.
Production deployments should rotate to asymmetric keys (RS256) and use a
trusted JWT issuer. The token carries `sub`, `email`, `name`, and `provider`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from translator_api.security.identity import UserIdentity


class SessionError(RuntimeError):
    pass


DEFAULT_TTL = 60 * 60 * 8


@dataclass(frozen=True)
class SessionSettings:
    secret: str
    issuer: str = "translator"
    ttl_seconds: int = DEFAULT_TTL


def load_session_settings() -> SessionSettings:
    secret = os.environ.get("TRANSLATOR_SESSION_SECRET", "")
    if not secret:
        secret = "phase4-insecure-dev-secret-do-not-use-in-prod"
    ttl = int(os.environ.get("TRANSLATOR_SESSION_TTL", str(DEFAULT_TTL)))
    return SessionSettings(secret=secret, ttl_seconds=ttl)


def issue_session_jwt(identity: UserIdentity, *, settings: SessionSettings | None = None) -> str:
    cfg = settings or load_session_settings()
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": identity.user_id,
        "email": identity.email,
        "name": identity.display_name,
        "provider": identity.provider,
        "iss": cfg.issuer,
        "iat": int(time.time()),
        "exp": int(time.time()) + cfg.ttl_seconds,
    }
    segments = (
        _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
    )
    signing_input = ".".join(segments).encode("utf-8")
    signature = hmac.new(cfg.secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return ".".join([*segments, _b64url(signature)])


def verify_session_jwt(token: str, *, settings: SessionSettings | None = None) -> UserIdentity:
    if not token or token.count(".") != 2:
        raise SessionError("malformed token")
    cfg = settings or load_session_settings()
    header_b64, payload_b64, signature_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected = hmac.new(cfg.secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(signature_b64)):
        raise SessionError("signature mismatch")
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if int(time.time()) > int(payload.get("exp", 0)):
        raise SessionError("token expired")
    return UserIdentity(
        user_id=str(payload.get("sub")),
        email=str(payload.get("email", "")),
        display_name=payload.get("name"),
        provider=str(payload.get("provider", "unknown")),
    )


def _b64url(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(token: str) -> bytes:
    padding = "=" * (-len(token) % 4)
    return base64.urlsafe_b64decode(token + padding)