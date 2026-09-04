"""Pydantic schemas for ASR + alignment outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AlignedWord(BaseModel):
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    speaker_id: str | None = None
    score: float = Field(ge=0, le=1)


class TranscriptSegment(BaseModel):
    id: str
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    speaker_id: str | None = None
    words: list[AlignedWord] = Field(default_factory=list)


class AlignmentResult(BaseModel):
    language: str
    model_id: str
    model_version: str
    segments: list[TranscriptSegment]
    speaker_count: int = 0
    duration_ms: int = Field(ge=0)
