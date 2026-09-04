"""Transcript, transcript_segment, transcript_word."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from translator_api.models import Base


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (UniqueConstraint("asset_id", "signature", name="uq_transcripts_asset_signature"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    language_detected: Mapped[str | None] = mapped_column(String(16))
    language_profile: Mapped[str | None] = mapped_column(String(32))
    model_id: Mapped[str | None] = mapped_column(String(128))
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Relationship for eager loading
    segments: Mapped[list["TranscriptSegment"]] = relationship("TranscriptSegment", lazy="raise")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    transcript_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    quality_flags: Mapped[dict | None] = mapped_column(JSONB)
    speaker_label: Mapped[str | None] = mapped_column(String(64))


class TranscriptWord(Base):
    __tablename__ = "transcript_words"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    segment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
