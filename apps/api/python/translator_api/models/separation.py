"""Audio separation tracks persistence.

One project can have multiple SeparationTracks per kind (vocals, music, sfx).
Each track row references a storage key in S3 (or local storage).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


# Canonical track kinds. Some providers emit more granular (e.g. `vocals`,
# `drums`, `bass`, `other`). We collapse to the four canonical kinds unless
# `extra_kinds` is set on the project.
DEFAULT_KINDS = ("vocals", "music", "sfx", "instrumental")


class SeparationTrack(Base):
    __tablename__ = "separation_tracks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=44100)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
