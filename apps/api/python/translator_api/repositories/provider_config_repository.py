"""Provider config repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import ProviderConfig


class ProviderConfigRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self, provider_kind: str, project_id: UUID | None) -> ProviderConfig | None:
        stmt = (
            select(ProviderConfig)
            .where(ProviderConfig.provider_kind == provider_kind, ProviderConfig.is_active.is_(True))
            .order_by(ProviderConfig.project_id.is_(None), ProviderConfig.project_id.desc())
            .limit(1)
        )
        if project_id is not None:
            stmt = stmt.where((ProviderConfig.project_id == project_id) | (ProviderConfig.project_id.is_(None)))
        else:
            stmt = stmt.where(ProviderConfig.project_id.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, config: ProviderConfig) -> ProviderConfig:
        self.db.add(config)
        self.db.flush()
        return config