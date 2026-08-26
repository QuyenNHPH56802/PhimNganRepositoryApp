"""Project, project members, project settings."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_language: Mapped[str] = mapped_column(String(8), nullable=False, default="zh")
    target_language: Mapped[str] = mapped_column(String(8), nullable=False, default="vi")
    quality_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="standard_dubbing")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    language_profile: Mapped[str] = mapped_column(String(32), nullable=False, default="zh-vi")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="editor")
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectSettings(Base):
    __tablename__ = "project_settings"

    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    genre: Mapped[str | None] = mapped_column(String(64))
    style_preset: Mapped[str | None] = mapped_column(String(32))
    subtitle_mode: Mapped[str | None] = mapped_column(String(32))
    accent_preference: Mapped[str | None] = mapped_column(String(32))
    audio_mode: Mapped[str | None] = mapped_column(String(32))
    music_level: Mapped[str | None] = mapped_column(String(16))
    dubbing_overrides: Mapped[dict | None] = mapped_column(JSONB)