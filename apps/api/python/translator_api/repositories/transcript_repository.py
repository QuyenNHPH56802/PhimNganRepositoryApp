"""Transcript repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Transcript, TranscriptSegment, TranscriptWord


class TranscriptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, transcript_id: UUID) -> Transcript | None:
        return self.db.get(Transcript, transcript_id)

    def find_by_signature(self, asset_id: UUID, signature: str) -> Transcript | None:
        stmt = select(Transcript).where(Transcript.asset_id == asset_id, Transcript.signature == signature)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, transcript: Transcript, segments: list[TranscriptSegment], words: list[TranscriptWord]) -> Transcript:
        transcript.created_at = datetime.now(timezone.utc)
        self.db.add(transcript)
        self.db.flush()
        for segment in segments:
            self.db.add(segment)
        for word in words:
            self.db.add(word)
        self.db.flush()
        return transcript