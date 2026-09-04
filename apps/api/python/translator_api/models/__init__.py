"""SQLAlchemy ORM models for the translator platform.

Module split mirrors the ERD groups (docs/ERD.md). Every file declares one
table; this __init__ re-exports them so Alembic autogenerate can pick them
all up from Base.metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


from translator_api.models.assets import Asset  # noqa: E402,F401
from translator_api.models.audio import AudioSegment, AudioTrack  # noqa: E402,F401
from translator_api.models.characters import CharacterAlias, CharacterProfile  # noqa: E402,F401
from translator_api.models.export import Export, RenderJob  # noqa: E402,F401
from translator_api.models.glossary import Glossary, GlossaryTerm  # noqa: E402,F401
from translator_api.models.webhook import Webhook, WebhookDelivery  # noqa: E402,F401
from translator_api.models.ocr import OcrRegion, TextRemovalJob  # noqa: E402,F401
from translator_api.models.separation import SeparationTrack  # noqa: E402,F401
from translator_api.models.voice import TtsSegment, VoiceCloneSample, VoiceProfile  # noqa: E402,F401
from translator_api.models.misc import AuditLog, ProviderConfig  # noqa: E402,F401
from translator_api.models.project import Project, ProjectMember, ProjectSettings  # noqa: E402,F401
from translator_api.models.speaker import Speaker, SpeakerSegment  # noqa: E402,F401
from translator_api.models.subtitle import SubtitleSegment, SubtitleTrack  # noqa: E402,F401
from translator_api.models.translation import TranslationSegment, TranslationVersion  # noqa: E402,F401
from translator_api.models.transcript import Transcript, TranscriptSegment, TranscriptWord  # noqa: E402,F401
from translator_api.models.user import User  # noqa: E402,F401
from translator_api.models.workflow import Workflow, WorkflowStep  # noqa: E402,F401

__all__ = [
    "Base",
    "User",
    "Project",
    "ProjectMember",
    "ProjectSettings",
    "Asset",
    "Transcript",
    "TranscriptSegment",
    "TranscriptWord",
    "Speaker",
    "SpeakerSegment",
    "CharacterProfile",
    "CharacterAlias",
    "Glossary",
    "GlossaryTerm",
    "TranslationVersion",
    "TranslationSegment",
    "VoiceProfile",
    "VoiceCloneSample",
    "TtsSegment",
    "AudioTrack",
    "AudioSegment",
    "SubtitleTrack",
    "SubtitleSegment",
    "Workflow",
    "WorkflowStep",
    "RenderJob",
    "Export",
    "OcrRegion",
    "TextRemovalJob",
    "SeparationTrack",
    "Webhook",
    "WebhookDelivery",
    "ProviderConfig",
    "AuditLog",
]


TimestampMixin_default = mapped_column(DateTime(timezone=True), default=_utcnow)
