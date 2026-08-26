"""Pydantic schemas re-exported as a package."""

from datasets.golden import (
    Domain,
    GoldenManifest,
    GoldenOcrDetection,
    GoldenOcrImage,
    GoldenSentence,
    GoldenSubtitle,
    GoldenTextRemoval,
    GoldenTranslation,
    GoldenTtsSample,
    License,
    Provenance,
    SpeakerGender,
)

__all__ = [
    "Domain",
    "GoldenManifest",
    "GoldenOcrDetection",
    "GoldenOcrImage",
    "GoldenSentence",
    "GoldenSubtitle",
    "GoldenTextRemoval",
    "GoldenTranslation",
    "GoldenTtsSample",
    "License",
    "Provenance",
    "SpeakerGender",
]