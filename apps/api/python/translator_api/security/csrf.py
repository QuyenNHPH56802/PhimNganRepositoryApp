"""CSRF token (double-submit cookie)."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "translator_csrf"


class CsrfTokenError(RuntimeError):
    pass


def _secret() -> bytes:
    base = os.environ.get("TRANSLATOR_SESSION_SECRET", "phase4-insecure-dev-secret-do-not-use-in-prod")
    return base.encode("utf-8")


def issue_csrf_token() -> str:
    nonce = secrets.token_urlsafe(16)
    digest = hmac.new(_secret(), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{nonce}.{digest}"


def verify_csrf_token(token: str) -> None:
    if not token or token.count(".") != 1:
        raise CsrfTokenError("malformed csrf token")
    nonce, digest = token.split(".", 1)
    expected = hmac.new(_secret(), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, digest):
        raise CsrfTokenError("csrf token mismatch")