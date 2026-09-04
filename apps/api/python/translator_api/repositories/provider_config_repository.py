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

    def get(self, config_id: UUID) -> ProviderConfig | None:
        return self.db.get(ProviderConfig, config_id)

    def list_for_project(self, project_id: UUID) -> list[ProviderConfig]:
        stmt = select(ProviderConfig).where(
            (ProviderConfig.project_id == project_id) | (ProviderConfig.project_id.is_(None))
        )
        return list(self.db.execute(stmt).scalars())

    def add(self, config: ProviderConfig) -> ProviderConfig:
        self.db.add(config)
        self.db.flush()
        return config

    def upsert(
        self,
        project_id: UUID | None,
        provider_kind: str,
        provider_id: str,
        config: dict | None,
        is_active: bool = True,
    ) -> ProviderConfig:
        """Insert or update a provider config keyed on (project_id, provider_kind, provider_id)."""
        if project_id is not None:
            stmt = select(ProviderConfig).where(
                ProviderConfig.project_id == project_id,
                ProviderConfig.provider_kind == provider_kind,
                ProviderConfig.provider_id == provider_id,
            )
        else:
            stmt = select(ProviderConfig).where(
                ProviderConfig.project_id.is_(None),
                ProviderConfig.provider_kind == provider_kind,
                ProviderConfig.provider_id == provider_id,
            )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing is not None:
            existing.config = config
            existing.is_active = is_active
            self.db.flush()
            return existing
        row = ProviderConfig(
            project_id=project_id,
            provider_kind=provider_kind,
            provider_id=provider_id,
            config=config,
            is_active=is_active,
        )
        self.db.add(row)
        self.db.flush()
        return row
