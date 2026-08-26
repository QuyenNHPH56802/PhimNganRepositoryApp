"""Render_job + export."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workflow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    output_storage_key: Mapped[str | None] = mapped_column(String(1024))
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    validation: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Export(Base):
    __tablename__ = "exports"
    __table_args__ = (UniqueConstraint("render_job_id", "format", name="uq_exports_render_format"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    render_job_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("render_jobs.id", ondelete="CASCADE"), nullable=False)
    format: Mapped[str] = mapped_column(String(8), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    size: Mapped[int | None] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signed_url_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))