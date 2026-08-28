"""FastAPI shared dependencies."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.security.identity import UserIdentity
from translator_api.security.session import SessionError, verify_session_jwt


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid auth scheme",
        )
    return token


def get_identity(authorization: str | None = Header(default=None)) -> UserIdentity:
    token = _extract_bearer(authorization)
    try:
        return verify_session_jwt(token)
    except SessionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db
