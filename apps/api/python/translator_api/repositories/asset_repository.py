"""Asset repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Asset


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, asset_id: UUID) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def list_for_project(self, project_id: UUID) -> list[Asset]:
        stmt = select(Asset).where(Asset.project_id == project_id).order_by(Asset.uploaded_at.desc())
        return list(self.db.execute(stmt).scalars())

    def add(self, asset: Asset) -> Asset:
        asset.uploaded_at = datetime.now(timezone.utc)
        self.db.add(asset)
        self.db.flush()
        return asset

    def delete(self, asset: Asset) -> None:
        self.db.delete(asset)