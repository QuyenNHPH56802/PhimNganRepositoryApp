"""Translation version + segment."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from translator_api.models import Base


class TranslationVersion(Base):
    __tablename__ = "translation_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "transcript_id", "version", name="uq_translation_versions"),
        UniqueConstraint("transcript_id", "signature", name="uq_translation_signature"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    transcript_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    glossary_snapshot_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("glossaries.id"))
    character_bible_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    style_preset: Mapped[str | None] = mapped_column(String(32))
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship for eager loading
    segments: Mapped[list["TranslationSegment"]] = relationship("TranslationSegment", lazy="raise")


class TranslationSegment(Base):
    __tablename__ = "translation_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    translation_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("translation_versions.id", ondelete="CASCADE"), nullable=False)
    transcript_segment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    tts_text: Mapped[str | None] = mapped_column(Text)
    applied_glossary_terms: Mapped[dict | None] = mapped_column(JSONB)
    applied_aliases: Mapped[dict | None] = mapped_column(JSONB)
    qa_status: Mapped[str | None] = mapped_column(String(16))
    qa_issues: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Float)
