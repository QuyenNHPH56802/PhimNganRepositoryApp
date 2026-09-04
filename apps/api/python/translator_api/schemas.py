"""Pydantic request/response models for the public REST API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from translator_shared.workflows import QualityMode, WorkflowStatus


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    quality_mode: QualityMode = QualityMode.BALANCED
    language_profile: str = Field(default="zh-vi", max_length=32)
    source_language: str = Field(default="zh", max_length=8)
    target_language: str = Field(default="vi", max_length=8)
    tts_provider_id: str | None = Field(default="edge_tts", max_length=64)
    tts_config: dict | None = None
    translate_provider_id: str | None = Field(default="local_llm", max_length=64)
    translate_config: dict | None = None


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    quality_mode: QualityMode
    status: WorkflowStatus
    created_at: datetime


class ProjectUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int


class AssetPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    mime: str = Field(min_length=1, max_length=128)
    size: int = Field(ge=0, le=10 * 1024 * 1024 * 1024)


class AssetPresignResponse(BaseModel):
    key: str
    url: str
    headers: dict[str, str]
    expires_in: int


class WorkflowTriggerRequest(BaseModel):
    quality_mode: QualityMode | None = None
    asset_id: UUID | None = None


class WorkflowTriggerResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: WorkflowStatus = WorkflowStatus.PROCESSING


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: WorkflowStatus
    last_error: str | None = None


class WorkflowStepResponse(BaseModel):
    id: UUID
    name: str
    status: str
    attempt: int
    progress_pct: int
    progress_message: str | None = None
    artifact_signature: str | None = None


class ProviderConfigUpsert(BaseModel):
    provider_kind: str = Field(min_length=1, max_length=32)
    provider_id: str = Field(min_length=1, max_length=64)
    config: dict = Field(default_factory=dict)
    is_active: bool = True


class ProviderConfigResponse(BaseModel):
    id: UUID
    provider_kind: str
    provider_id: str
    config: dict
    is_active: bool


class AuditLogResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    payload: dict | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int


class ConsentStateResponse(BaseModel):
    voice_profile_id: UUID
    status: str
    evidence_key: str | None = None


class ProjectConsentRequest(BaseModel):
    evidence_key: str = Field(min_length=1, max_length=1024)


class QualityModeRequest(BaseModel):
    mode: str = Field(pattern="^(fast|balanced|high)$")


class QualityModeResponse(BaseModel):
    project_id: UUID
    mode: str
    policy: dict


class MemberAddRequest(BaseModel):
    user_id: str = Field(min_length=36, max_length=36)
    role: str = Field(default="viewer", pattern="^(owner|editor|viewer)$")


class MemberResponse(BaseModel):
    user_id: str
    role: str
    added_at: datetime


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
