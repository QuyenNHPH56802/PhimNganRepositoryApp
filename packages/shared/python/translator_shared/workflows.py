"""Workflow-related enums shared by API and worker.

`QualityMode` carries three production tiers (`fast` / `balanced` /
`high`). The legacy names (`only_subtitle` / `standard_dubbing` /
`quality_dubbing`) were removed in v1.0.0 — see
`docs/deprecation.md` for the migration timeline.
"""

from __future__ import annotations

from enum import Enum


class QualityMode(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH = "high"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    READY = "ready"
    ARCHIVED = "archived"
    FAILED = "failed"
