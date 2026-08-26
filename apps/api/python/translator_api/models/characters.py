"""Character profile + alias."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from translator_api.models import Base


class CharacterProfile(Base):
    __tablename__ = "character_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(16))
    age_group: Mapped[str | None] = mapped_column(String(16))
    role: Mapped[str | None] = mapped_column(String(64))
    preferred_pronouns: Mapped[dict | None] = mapped_column(JSONB)
    preferred_honorifics: Mapped[dict | None] = mapped_column(JSONB)
    default_voice_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("voice_profiles.id"))


class CharacterAlias(Base):
    __tablename__ = "character_aliases"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    character_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("character_profiles.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str | None] = mapped_column(String(16))
    source_pattern: Mapped[str | None] = mapped_column(String(255))