"""Speaker and speaker_segment."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String

from translator_api.models import Base


class Speaker(Base):
    __tablename__ = "speakers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    raw_label: Mapped[str] = mapped_column(String(64), nullable=False)
    character_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("character_profiles.id"))
    display_name: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[str | None] = mapped_column(String(16))
    age_group: Mapped[str | None] = mapped_column(String(16))


class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    speaker_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("speakers.id", ondelete="CASCADE"), nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("transcript_segments.id"))
    confidence: Mapped[float | None] = mapped_column(Float)