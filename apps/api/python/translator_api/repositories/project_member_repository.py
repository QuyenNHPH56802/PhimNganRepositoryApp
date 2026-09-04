"""Project member repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import ProjectMember


class ProjectMemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, project_id: UUID) -> list[ProjectMember]:
        stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
        return list(self.db.execute(stmt).scalars())

    def add(self, project_id: UUID, user_id: UUID, role: str) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            added_at=datetime.now(timezone.utc),
        )
        self.db.add(member)
        self.db.flush()
        return member

    def remove(self, project_id: UUID, user_id: UUID) -> None:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        member = self.db.execute(stmt).scalar_one_or_none()
        if member is not None:
            self.db.delete(member)
