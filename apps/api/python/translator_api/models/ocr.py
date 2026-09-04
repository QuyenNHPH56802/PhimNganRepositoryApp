"""OCR detection + text removal job."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class OcrDetection(Base):
    __tablename__ = "ocr_detections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSONB, nullable=False)
    frame_ts_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    model_id: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str | None] = mapped_column(String(8))


class TextRemovalJob(Base):
    __tablename__ = "text_removal_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    strategy: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    output_storage_key: Mapped[str | None] = mapped_column(String(1024))
    bbox_payload: Mapped[dict | None] = mapped_column(JSONB)
