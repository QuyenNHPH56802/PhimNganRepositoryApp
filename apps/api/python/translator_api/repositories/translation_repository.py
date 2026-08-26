"""Translation version repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import TranslationVersion


class TranslationVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, version_id: UUID) -> TranslationVersion | None:
        return self.db.get(TranslationVersion, version_id)

    def latest_for_transcript(self, transcript_id: UUID) -> TranslationVersion | None:
        stmt = (
            select(TranslationVersion)
            .where(TranslationVersion.transcript_id == transcript_id)
            .order_by(TranslationVersion.version.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def next_version(self, transcript_id: UUID) -> int:
        current = self.latest_for_transcript(transcript_id)
        return 1 if current is None else current.version + 1

    def add(self, version: TranslationVersion) -> TranslationVersion:
        version.created_at = datetime.now(timezone.utc)
        self.db.add(version)
        self.db.flush()
        return version