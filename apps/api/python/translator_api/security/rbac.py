"""Role enum & RBAC decorators."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.models import Project, ProjectMember
from translator_api.security.identity import UserIdentity
from translator_api.security.session import SessionError, verify_session_jwt


class Role(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_RANK: dict[Role, int] = {Role.OWNER: 30, Role.EDITOR: 20, Role.VIEWER: 10}


def role_at_least(role: Role, minimum: Role) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[minimum]


def current_identity(authorization: str = "") -> UserIdentity:
    """Resolve identity from `Authorization: Bearer <jwt>` header.

    Phase 4 keeps the helper package-local; routers import it via
    `Depends(current_identity)` after extracting the header.
    """

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid auth scheme")
    try:
        return verify_session_jwt(token)
    except SessionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_role(minimum: Role):
    def _dep(authorization: str = "") -> UserIdentity:
        identity = current_identity(authorization)
        return identity

    return _dep


def require_project_role(project_id: UUID, minimum: Role, *, db: Session, identity: UserIdentity) -> None:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    if project.owner_id == UUID(identity.user_id):
        return
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == UUID(identity.user_id)
    )
    membership = db.execute(stmt).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member")
    if not role_at_least(Role(membership.role), minimum):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"role {membership.role} < {minimum.value}")