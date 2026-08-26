"""Shared Pydantic schemas for ASR / alignment / diarization providers.

These are the canonical output shapes used across API + worker. They live
in translator_shared so that the API can serialize them directly and the
worker can emit them without an extra adapter.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from translator_shared.providers import ArtifactSignature


class AsrSegment(BaseModel):
    idx: int
    start_ms: int
    end_ms: int
    text: str
    speaker_label: str | None = None
    no_speech_prob: float | None = None


class AsrWord(BaseModel):
    idx: int
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


class AsrResponse(BaseModel):
    language: str
    language_probability: float | None = None
    duration_ms: int
    model_id: str
    model_version: str
    segments: list[AsrSegment]
    words: list[AsrWord]
    signature: ArtifactSignature
    extras: dict[str, str] = Field(default_factory=dict)


class AlignedWord(BaseModel):
    idx: int
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


class AlignedSegment(BaseModel):
    idx: int
    start_ms: int
    end_ms: int
    text: str
    words: list[AlignedWord]


class AlignResponse(BaseModel):
    language: str
    model_id: str
    model_version: str
    segments: list[AlignedSegment]
    signature: ArtifactSignature


class SpeakerTurn(BaseModel):
    speaker_label: str
    start_ms: int
    end_ms: int


class DiarizeResponse(BaseModel):
    model_id: str
    model_version: str
    num_speakers: int
    turns: list[SpeakerTurn]
    signature: ArtifactSignature