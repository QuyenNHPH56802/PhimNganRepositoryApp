"""Standalone auth dependency — no circular imports with routers modules.

Single-user mode: this app is intended to be used by one person. Every
request is automatically authenticated as the owner user (provisioned on
first call). There is no login flow.

Both routers.py and routers_governance.py import get_identity from here
instead of from each other, breaking the import cycle.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.db import SessionLocal
from translator_api.models import User
from translator_api.security.identity import UserIdentity

# Fixed UUID used for the single owner account.
OWNER_USER_ID = "00000000-0000-0000-0000-000000000001"
OWNER_EMAIL = "owner@localhost"
OWNER_DISPLAY_NAME = "Owner"


def _ensure_owner_user() -> None:
    """Provision the owner user row if it does not yet exist.

    Uses its own short-lived session so this can run outside a request.
    """
    from datetime import datetime, timezone
    session: Session = SessionLocal()
    try:
        existing = session.execute(
            select(User).where(User.id == UUID(OWNER_USER_ID))
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                User(
                    id=UUID(OWNER_USER_ID),
                    email=OWNER_EMAIL,
                    display_name=OWNER_DISPLAY_NAME,
                    is_admin=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()
    finally:
        session.close()


def _load_identity() -> UserIdentity:
    _ensure_owner_user()
    return UserIdentity(
        user_id=OWNER_USER_ID,
        email=OWNER_EMAIL,
        display_name=OWNER_DISPLAY_NAME,
        provider="single-user",
    )


def get_identity(
    authorization: str | None = Header(default=None, alias="authorization"),
) -> UserIdentity:
    """Resolve the identity for the current request.

    In single-user mode we always return the provisioned owner; an
    invalid bearer token is an explicit 401 so misconfigured clients
    are not silently masked.
    """
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid auth scheme",
            )
    return _load_identity()


# Backwards-compatible alias used by newer routers (glossary, etc.) that
# follow the standard FastAPI `get_current_user_*` naming convention.
get_current_user_optional = get_identity
