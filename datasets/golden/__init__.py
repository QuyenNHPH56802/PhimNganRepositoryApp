"""Golden dataset schemas (Pydantic)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Domain(str, Enum):
    NEWS = "news"
    VLOG = "vlog"
    REVIEW = "review"
    DRAMA = "drama"
    NARRATION = "narration"


class SpeakerGender(str, Enum):
    M = "m"
    F = "f"
    X = "x"


class License(str, Enum):
    CC_BY_SA_4 = "CC-BY-SA-4.0"
    CC_BY_4 = "CC-BY-4.0"
    CC0 = "CC0"


class Provenance(BaseModel):
    contributor: str
    source: Literal["in-house", "synthetic", "third-party"]
    reference: str | None = None
    notes: str | None = None


class GoldenSentence(BaseModel):
    id: str
    zh: str
    vi: str
    audio_key: str | None = None
    domain: Domain
    speaker_gender: SpeakerGender = SpeakerGender.X
    tags: list[str] = Field(default_factory=list)
    license: License = License.CC_BY_SA_4
    provenance: Provenance


class GoldenTranslation(BaseModel):
    id: str
    sentence_id: str
    model_translation: str
    judge_label: Literal["correct", "minor", "major"]
    notes: str | None = None


class GoldenSubtitle(BaseModel):
    id: str
    sentence_id: str
    vi: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    cps: float = Field(ge=0)


class GoldenTtsSample(BaseModel):
    id: str
    sentence_id: str
    vi: str
    audio_key: str | None = None
    sample_rate: int = 22050
    speaker_id: str
    duration_ms: int = Field(ge=0)


class GoldenOcrDetection(BaseModel):
    text: str
    bbox: list[dict[str, int]]
    frame_ts_ms: int
    confidence: float


class GoldenOcrImage(BaseModel):
    id: str
    image_key: str
    detections: list[GoldenOcrDetection]


class GoldenTextRemoval(BaseModel):
    id: str
    source_image_key: str
    expected_image_key: str
    strategy: Literal["inpaint_lama", "inpaint_anything", "telea"]
    detections: list[GoldenOcrDetection]


class GoldenManifest(BaseModel):
    name: str
    version: str
    license: License
    sources: list[Provenance]
    record_count: int
    audio_total_seconds: float = 0.0
    retention: str = "internal only"
    domains: list[Domain] = Field(default_factory=list)