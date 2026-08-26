"""Shared Pydantic schemas for translation, QA, subtitle, TTS, separation,
mix, render, export, and cleanup providers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from translator_shared.providers import ArtifactSignature


class TranslationSegment(BaseModel):
    idx: int
    display_text: str
    tts_text: str
    confidence: float | None = None
    applied_glossary_terms: list[str] = Field(default_factory=list)
    applied_aliases: list[str] = Field(default_factory=list)


class TranslationResponse(BaseModel):
    provider_id: str
    model_id: str
    prompt_version: str
    segments: list[TranslationSegment]
    signature: ArtifactSignature


class QaIssue(BaseModel):
    kind: str
    segment_idx: int | None = None
    message: str
    severity: str


class QaStats(BaseModel):
    ratio_min: float | None = None
    ratio_max: float | None = None
    pinyin_leak_count: int = 0
    untranslated_count: int = 0
    glossary_misses: int = 0


class QaReport(BaseModel):
    passed: bool
    qa_status: str
    issues: list[QaIssue]
    stats: QaStats


class SubtitleLine(BaseModel):
    idx: int
    start_ms: int
    end_ms: int
    text: str


class SubtitleResponse(BaseModel):
    track_id: UUID | None = None
    segments: list[SubtitleLine]
    signature: ArtifactSignature


class TtsResponse(BaseModel):
    voice_profile_id: UUID | None = None
    audio_storage_key: str
    duration_ms: int
    sample_rate: int
    signature: ArtifactSignature
    fallback_used: bool = False


class SeparationResponse(BaseModel):
    vocals_key: str
    background_key: str
    method: str
    duration_ms: int
    signature: ArtifactSignature


class AudioMixResponse(BaseModel):
    output_key: str
    duration_ms: int
    sample_rate: int
    signature: ArtifactSignature


class RenderResponse(BaseModel):
    output_key: str
    duration_ms: int
    validation: dict
    signature: ArtifactSignature


class ExportResponse(BaseModel):
    export_id: UUID | None = None
    storage_key: str
    size_bytes: int
    checksum_sha256: str
    format: str
    signature: ArtifactSignature


class CleanupReport(BaseModel):
    deleted_objects: list[str] = Field(default_factory=list)
    kept_objects: list[str] = Field(default_factory=list)
    scanned_at: datetime