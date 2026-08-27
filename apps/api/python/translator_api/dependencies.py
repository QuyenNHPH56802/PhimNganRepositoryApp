"""Backward-compatibility shim for `get_db` / `get_identity`.

`get_db` is the SQLAlchemy session dependency already defined in
`translator_api.db`. `get_identity` resolves the bearer token via the
session JWT verifier (same logic `routers_governance._identity` uses).
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from translator_api.db import get_db
from translator_api.security.identity import UserIdentity
from translator_api.security.session import verify_session_jwt

__all__ = ["get_db", "get_identity", "UserIdentity"]


def get_identity(authorization: str | None = Header(default=None)) -> UserIdentity:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid auth scheme"
        )
    try:
        return verify_session_jwt(token)
    except Exception as exc:  # noqa: BLE001 — surface as 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {exc}"
        ) from exc
