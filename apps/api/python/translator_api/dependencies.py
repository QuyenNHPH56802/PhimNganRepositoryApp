"""FastAPI shared dependencies."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.security.identity import UserIdentity
from translator_api.auth_dependency import OWNER_USER_ID, OWNER_EMAIL, OWNER_DISPLAY_NAME


def _load_identity() -> UserIdentity:
    return UserIdentity(
        user_id=OWNER_USER_ID,
        email=OWNER_EMAIL,
        display_name=OWNER_DISPLAY_NAME,
        provider="single-user",
    )


def get_identity(authorization: str | None = Header(default=None)) -> UserIdentity:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid auth scheme",
            )
    return _load_identity()


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db
