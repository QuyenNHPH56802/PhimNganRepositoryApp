"""Subtitle track + segment."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class SubtitleTrack(Base):
    __tablename__ = "subtitle_tracks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(8))
    format: Mapped[str] = mapped_column(String(8), nullable=False)


class SubtitleSegment(Base):
    __tablename__ = "subtitle_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subtitle_track_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("subtitle_tracks.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    translation_segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("translation_segments.id"))
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
