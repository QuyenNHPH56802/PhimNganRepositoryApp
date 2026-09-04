"""Speaker repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Speaker, SpeakerSegment


class SpeakerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, project_id: UUID) -> list[Speaker]:
        stmt = select(Speaker).where(Speaker.project_id == project_id)
        return list(self.db.execute(stmt).scalars())

    def upsert(self, speaker: Speaker) -> Speaker:
        self.db.add(speaker)
        self.db.flush()
        return speaker

    def add_segments(self, segments: list[SpeakerSegment]) -> None:
        for seg in segments:
            self.db.add(seg)
        self.db.flush()
