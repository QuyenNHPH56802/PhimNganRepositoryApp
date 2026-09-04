"""Voice profile + tts_segment."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    speaker_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("speakers.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    default_accent: Mapped[str | None] = mapped_column(String(32))
    reference_audio_key: Mapped[str | None] = mapped_column(String(1024))
    reference_audio_hash: Mapped[str | None] = mapped_column(String(64))
    embedding_storage_key: Mapped[str | None] = mapped_column(String(1024))
    consent_status: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_evidence_key: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TtsSegment(Base):
    __tablename__ = "tts_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    voice_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("voice_profiles.id"), nullable=False)
    translation_segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("translation_segments.id"))
    audio_segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("audio_segments.id"))
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    sample_rate: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VoiceCloneSample(Base):
    """A voice sample uploaded to drive a voice clone.

    A user uploads a clean audio snippet (typically 6-30s of single speaker);
    a voice cloning provider derives an embedding and may generate a preview
    TTS to validate the quality.
    """

    __tablename__ = "voice_clone_samples"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    speaker_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("speakers.id", ondelete="SET NULL"))
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_storage_key: Mapped[str | None] = mapped_column(String(1024))
    preview_storage_key: Mapped[str | None] = mapped_column(String(1024))
    quality_score: Mapped[float | None] = mapped_column(Float)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Status: queued | running | completed | failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
