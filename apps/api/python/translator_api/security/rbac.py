"""Role enum & RBAC helpers."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Project, ProjectMember
from translator_api.security.identity import UserIdentity


class Role(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


ROLE_RANK: dict[Role, int] = {Role.OWNER: 30, Role.EDITOR: 20, Role.VIEWER: 10}


def role_at_least(role: Role, minimum: Role) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[minimum]


def require_project_role(project_id: UUID, minimum: Role, *, db: Session, identity: UserIdentity) -> None:
    """Enforce project membership.

    In single-user mode the identity is always the owner, so any project
    they can reference is implicitly accessible.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    try:
        owner_uuid = UUID(identity.user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid identity")
    if project.owner_id == owner_uuid:
        return
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == owner_uuid
    )
    membership = db.execute(stmt).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member")
    if not role_at_least(Role(membership.role), minimum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"role {membership.role} < {minimum.value}",
        )