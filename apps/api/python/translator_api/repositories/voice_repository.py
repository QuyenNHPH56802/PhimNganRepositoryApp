"""Voice profile repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import VoiceProfile


class VoiceProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, voice_profile_id: UUID) -> VoiceProfile | None:
        return self.db.get(VoiceProfile, voice_profile_id)

    def list_for_project(self, project_id: UUID) -> list[VoiceProfile]:
        stmt = select(VoiceProfile).where(VoiceProfile.project_id == project_id)
        return list(self.db.execute(stmt).scalars())

    def add(self, voice_profile: VoiceProfile) -> VoiceProfile:
        voice_profile.created_at = datetime.now(timezone.utc)
        self.db.add(voice_profile)
        self.db.flush()
        return voice_profile
