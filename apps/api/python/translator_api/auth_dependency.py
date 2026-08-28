"""Standalone auth dependency — no circular imports with routers modules.

Both routers.py and routers_governance.py import get_identity from here
instead of from each other, breaking the import cycle."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from translator_api.security.identity import UserIdentity
from translator_api.security.session import SessionError, verify_session_jwt


def get_identity(
    authorization: str | None = Header(default=None, alias="authorization"),
) -> UserIdentity:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid auth scheme")
    try:
        return verify_session_jwt(token)
    except SessionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
