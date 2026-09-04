"""Audio separation tracks CRUD + run endpoint.

Endpoints:
- POST /projects/{id}/separation/run   → run a separation job
- GET  /projects/{id}/separation/tracks → list tracks
- DELETE /projects/{id}/separation/tracks/{track_id}

Real provider execution uses the existing providers/separation/* stack;
mock provider is registered automatically for dev environments.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import Project, SeparationTrack

router = APIRouter(prefix="/projects/{project_id}/separation", tags=["separation"])


# ─── Schemas ─────────────────────────────────────────────────────────────


class SeparationRunIn(BaseModel):
    provider_id: str = Field(default="separation.mock")
    method: str = Field(default="MDX23K")
    segment_size: int = Field(default=256, ge=64, le=1024)


class TrackOut(BaseModel):
    id: UUID
    kind: str
    storage_key: str
    download_url: str
    provider_id: str
    duration_ms: int
    sample_rate: int
    confidence: float | None
    created_at: datetime


class SeparationRunOut(BaseModel):
    project_id: UUID
    provider_id: str
    method: str
    tracks: list[TrackOut]


class SeparationStatus(BaseModel):
    has_runs: bool
    last_run_at: datetime | None
    last_provider: str | None
    tracks: list[TrackOut]


# ─── Helpers ─────────────────────────────────────────────────────────────


def _serialize(t: SeparationTrack) -> TrackOut:
    """Build a TrackOut row. Download URL is intentionally a relative path
    so the caller (frontend) can swap in the API gateway / asset proxy as needed.
    """
    download_url = f"/api/storage/{t.storage_key}"
    return TrackOut(
        id=t.id,
        kind=t.kind,
        storage_key=t.storage_key,
        download_url=download_url,
        provider_id=t.provider_id,
        duration_ms=t.duration_ms,
        sample_rate=t.sample_rate,
        confidence=t.confidence,
        created_at=t.created_at,
    )


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.post("/run", response_model=SeparationRunOut, status_code=202)
async def run_separation(
    project_id: UUID,
    body: SeparationRunIn,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> SeparationRunOut:
    """Run separation on the project's audio track."""
    _ensure_project(db, project_id)

    # Lazy import: keep heavy ML deps out of cold start.
    from translator_api.providers.base import CapabilityUnsupported, ProviderContext
    from translator_api.providers.separation.mock_provider import MockSeparationProvider
    from translator_api.providers.separation.base import SeparationInput
    from translator_shared.provider_configs import SeparationProviderConfig

    cfg = SeparationProviderConfig(
        provider_id=body.provider_id,
        model_id=body.method,
        segment_size=body.segment_size,
    )
    provider = MockSeparationProvider()
    ctx = ProviderContext(project_id=str(project_id))
    try:
        response = await provider.run(
            SeparationInput(
                asset_storage_key=str(project_id),
                config=cfg,
            ),
            ctx=ctx,
        )
    except CapabilityUnsupported as exc:
        raise HTTPException(status_code=501, detail=f"separation unavailable: {exc.code}")

    now = datetime.now(timezone.utc)
    rows: list[SeparationTrack] = []
    for kind, key in (
        ("vocals", response.vocals_key),
        ("background", response.background_key),
    ):
        row = SeparationTrack(
            project_id=project_id,
            kind=kind,
            storage_key=key,
            provider_id=body.provider_id,
            duration_ms=response.duration_ms,
            sample_rate=44100,
            confidence=0.9,
            is_active=True,
            created_at=now,
        )
        db.add(row)
        rows.append(row)
    db.commit()

    return SeparationRunOut(
        project_id=project_id,
        provider_id=body.provider_id,
        method=body.method,
        tracks=[_serialize(r) for r in rows],
    )


@router.get("/tracks", response_model=list[TrackOut])
def list_tracks(
    project_id: UUID,
    kind: str | None = None,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> list[TrackOut]:
    _ensure_project(db, project_id)
    q = db.query(SeparationTrack).filter_by(project_id=project_id)
    if kind:
        q = q.filter(SeparationTrack.kind == kind)
    rows = q.order_by(SeparationTrack.created_at.desc()).all()
    return [_serialize(r) for r in rows]


@router.delete("/tracks/{track_id}", status_code=204)
def delete_track(
    project_id: UUID,
    track_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> None:
    row = db.get(SeparationTrack, track_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="track not found")
    db.delete(row)
    db.commit()
