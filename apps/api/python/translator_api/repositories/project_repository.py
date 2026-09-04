"""Project repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def list(self, *, owner_id: UUID | None = None, limit: int = 50, offset: int = 0) -> list[Project]:
        stmt = select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
        if owner_id is not None:
            stmt = stmt.where(Project.owner_id == owner_id)
        return list(self.db.execute(stmt).scalars())

    def add(self, project: Project) -> Project:
        now = datetime.now(timezone.utc)
        project.created_at = now
        project.updated_at = now
        self.db.add(project)
        self.db.flush()
        return project

    def update_status(self, project: Project, status: str) -> Project:
        project.status = status
        project.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
