"""Voice cloning endpoints.

Endpoints:
- POST /projects/{id}/voice-clone/samples   → register a sample (storage_key + label)
- GET  /projects/{id}/voice-clone/samples   → list
- POST /projects/{id}/voice-clone/samples/{sid}/run → start cloning job
- GET  /projects/{id}/voice-clone/samples/{sid}      → detail
- DELETE /projects/{id}/voice-clone/samples/{sid}    → remove

Real provider execution uses the providers/voice/* stack; mock is registered
automatically for dev / tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import Project, VoiceCloneSample

router = APIRouter(prefix="/projects/{project_id}/voice-clone", tags=["voice-clone"])


# ─── Schemas ─────────────────────────────────────────────────────────────


class VoiceCloneSampleIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    sample_storage_key: str = Field(..., min_length=1, max_length=1024)
    speaker_id: UUID | None = None
    provider_id: str = Field(default="voice.mock")
    duration_ms: int = Field(default=0, ge=0)
    text_preview: str | None = None


class VoiceCloneSampleOut(BaseModel):
    id: UUID
    project_id: UUID
    speaker_id: UUID | None
    label: str
    sample_storage_key: str
    sample_download_url: str
    provider_id: str
    embedding_storage_key: str | None
    embedding_download_url: str | None
    preview_storage_key: str | None
    preview_download_url: str | None
    quality_score: float | None
    duration_ms: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class VoiceCloneRunOut(BaseModel):
    sample_id: UUID
    provider_id: str
    quality_score: float | None
    embedding_storage_key: str | None
    preview_storage_key: str | None
    status: str


# ─── Helpers ─────────────────────────────────────────────────────────────


def _serialize(s: VoiceCloneSample) -> VoiceCloneSampleOut:
    return VoiceCloneSampleOut(
        id=s.id,
        project_id=s.project_id,
        speaker_id=s.speaker_id,
        label=s.label,
        sample_storage_key=s.sample_storage_key,
        sample_download_url=f"/api/storage/{s.sample_storage_key}",
        provider_id=s.provider_id,
        embedding_storage_key=s.embedding_storage_key,
        embedding_download_url=(
            f"/api/storage/{s.embedding_storage_key}" if s.embedding_storage_key else None
        ),
        preview_storage_key=s.preview_storage_key,
        preview_download_url=(
            f"/api/storage/{s.preview_storage_key}" if s.preview_storage_key else None
        ),
        quality_score=s.quality_score,
        duration_ms=s.duration_ms,
        status=s.status,
        error_message=s.error_message,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.get("/samples", response_model=list[VoiceCloneSampleOut])
def list_samples(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> list[VoiceCloneSampleOut]:
    _ensure_project(db, project_id)
    rows = (
        db.query(VoiceCloneSample)
        .filter_by(project_id=project_id)
        .order_by(VoiceCloneSample.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


@router.post("/samples", response_model=VoiceCloneSampleOut, status_code=201)
def create_sample(
    project_id: UUID,
    body: VoiceCloneSampleIn,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> VoiceCloneSampleOut:
    _ensure_project(db, project_id)
    now = datetime.now(timezone.utc)
    sample = VoiceCloneSample(
        project_id=project_id,
        speaker_id=body.speaker_id,
        label=body.label,
        sample_storage_key=body.sample_storage_key,
        provider_id=body.provider_id,
        duration_ms=body.duration_ms,
        status="queued",
        created_at=now,
        updated_at=now,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return _serialize(sample)


@router.post("/samples/{sample_id}/run", response_model=VoiceCloneRunOut)
async def run_clone(
    project_id: UUID,
    sample_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> VoiceCloneRunOut:
    """Run the cloning job for a sample. Updates the row in place."""
    sample = db.get(VoiceCloneSample, sample_id)
    if sample is None or sample.project_id != project_id:
        raise HTTPException(status_code=404, detail="sample not found")

    sample.status = "running"
    sample.updated_at = datetime.now(timezone.utc)
    db.commit()

    from translator_api.providers.base import CapabilityUnsupported, ProviderContext
    from translator_api.providers.voice.base import VoiceCloneInput
    from translator_api.providers.voice.mock_provider import MockVoiceCloneProvider
    from translator_api.providers.voice.xtts_provider import XttsVoiceCloneProvider

    provider = (
        XttsVoiceCloneProvider() if sample.provider_id == "voice.xtts" else MockVoiceCloneProvider()
    )
    ctx = ProviderContext(project_id=str(project_id))

    try:
        response = await provider.run(
            VoiceCloneInput(
                sample_storage_key=sample.sample_storage_key,
                provider_id=sample.provider_id,
                text_preview=None,
            ),
            ctx=ctx,
        )
    except CapabilityUnsupported as exc:
        sample.status = "failed"
        sample.error_message = f"{exc.code}: {exc}"
        sample.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=501, detail=f"clone provider unavailable: {exc.code}")

    sample.embedding_storage_key = response.embedding_storage_key
    sample.preview_storage_key = response.preview_storage_key
    sample.quality_score = response.quality_score
    sample.duration_ms = response.duration_ms or sample.duration_ms
    sample.status = "completed"
    sample.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sample)

    return VoiceCloneRunOut(
        sample_id=sample.id,
        provider_id=sample.provider_id,
        quality_score=sample.quality_score,
        embedding_storage_key=sample.embedding_storage_key,
        preview_storage_key=sample.preview_storage_key,
        status=sample.status,
    )


@router.get("/samples/{sample_id}", response_model=VoiceCloneSampleOut)
def get_sample(
    project_id: UUID,
    sample_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> VoiceCloneSampleOut:
    sample = db.get(VoiceCloneSample, sample_id)
    if sample is None or sample.project_id != project_id:
        raise HTTPException(status_code=404, detail="sample not found")
    return _serialize(sample)


@router.delete("/samples/{sample_id}", status_code=204)
def delete_sample(
    project_id: UUID,
    sample_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> None:
    sample = db.get(VoiceCloneSample, sample_id)
    if sample is None or sample.project_id != project_id:
        raise HTTPException(status_code=404, detail="sample not found")
    db.delete(sample)
    db.commit()
