"""Text removal jobs — kick off inpainting jobs over selected OCR regions.

A TextRemovalJob references:
- a source asset (the video or frame to clean)
- a list of OCR region IDs whose bboxes should be in-painted
- the chosen provider/strategy

The pipeline produces an output asset (cleaned video / frames) once finished.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import (
    Asset,
    OcrRegion,
    Project,
    TextRemovalJob,
)

router = APIRouter(prefix="/projects/{project_id}/text-removal", tags=["text-removal"])


# ─── Schemas ─────────────────────────────────────────────────────────────


class TextRemovalJobIn(BaseModel):
    provider_id: str = Field(default="text_removal.mock")
    strategy: Literal["inpaint_lama", "inpaint_anything", "telea"] = Field(
        default="telea"
    )
    region_ids: list[UUID] = Field(default_factory=list)
    asset_id: UUID | None = None  # if None, uses the project's latest asset


class TextRemovalJobOut(BaseModel):
    id: UUID
    project_id: UUID
    source_asset_id: UUID
    region_ids: list[str]
    provider_id: str
    strategy: str
    status: str
    output_asset_id: UUID | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TextRemovalJobCreateOut(BaseModel):
    job: TextRemovalJobOut
    region_count: int


# ─── Helpers ─────────────────────────────────────────────────────────────


def _serialize(j: TextRemovalJob) -> TextRemovalJobOut:
    return TextRemovalJobOut(
        id=j.id,
        project_id=j.project_id,
        source_asset_id=j.source_asset_id,
        region_ids=j.region_ids or [],
        provider_id=j.provider_id or "",
        strategy=(j.raw_payload or {}).get("strategy", "") if j.raw_payload else "",
        status=j.status,
        output_asset_id=j.output_asset_id,
        error_message=j.error_message,
        created_at=j.created_at,
        updated_at=j.updated_at,
    )


def _latest_asset(db: SA_Session, project_id: UUID) -> Asset | None:
    return (
        db.query(Asset)
        .filter_by(project_id=project_id)
        .order_by(Asset.created_at.desc())
        .first()
    )


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.get("/jobs", response_model=list[TextRemovalJobOut])
def list_jobs(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> list[TextRemovalJobOut]:
    _ensure_project(db, project_id)
    rows = (
        db.query(TextRemovalJob)
        .filter_by(project_id=project_id)
        .order_by(TextRemovalJob.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


@router.post("/jobs", response_model=TextRemovalJobCreateOut, status_code=201)
async def create_job(
    project_id: UUID,
    body: TextRemovalJobIn,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> TextRemovalJobCreateOut:
    """Create a text-removal job. Runs synchronously through the mock provider."""
    _ensure_project(db, project_id)

    asset = None
    if body.asset_id:
        asset = db.get(Asset, body.asset_id)
        if asset is None or asset.project_id != project_id:
            raise HTTPException(status_code=400, detail="asset_id does not belong to project")
    else:
        asset = _latest_asset(db, project_id)
    if asset is None:
        raise HTTPException(
            status_code=400,
            detail="no asset found for project; upload a video first",
        )

    # Validate regions belong to this project.
    region_count = 0
    if body.region_ids:
        rows = (
            db.query(OcrRegion)
            .filter(
                OcrRegion.id.in_(body.region_ids),
                OcrRegion.project_id == project_id,
            )
            .all()
        )
        region_count = len(rows)
        if region_count == 0:
            raise HTTPException(
                status_code=400,
                detail="none of the provided region_ids belong to this project",
            )

    now = datetime.now(timezone.utc)
    job = TextRemovalJob(
        id=uuid4(),
        project_id=project_id,
        source_asset_id=asset.id,
        region_ids=[str(r) for r in body.region_ids],
        provider_id=body.provider_id,
        status="running",
        raw_payload={"strategy": body.strategy, "region_count": region_count},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()

    # Run provider (sync for the mock; real impl would dispatch to a worker).
    from translator_api.providers.base import CapabilityUnsupported, ProviderContext
    from translator_api.providers.text_removal.mock_provider import MockTextRemovalProvider
    from translator_api.providers.text_removal.base import (
        TextRemovalInput,
        TextRemovalProvider,
    )

    provider: TextRemovalProvider
    if body.provider_id == "text_removal.mock":
        provider = MockTextRemovalProvider()
    else:
        provider = MockTextRemovalProvider()  # fallback

    ctx = ProviderContext(project_id=str(project_id))
    try:
        from translator_api.providers.ocr.base import OcrDetection

        detections = [
            OcrDetection(
                text="(preview)",
                bbox=[
                    {"x": 0, "y": 0, "w": 100, "h": 30},
                ],
                frame_ts_ms=0,
                confidence=1.0,
            )
        ]
        # In a full impl, we'd look up each region's bbox from the DB. For
        # the mock we just emit a placeholder detection to exercise the
        # pipeline.
        response = await provider.run(
            TextRemovalInput(
                asset_storage_key=asset.storage_key or str(asset.id),
                detections=detections,
                strategy=body.strategy,
            ),
            ctx=ctx,
        )
    except CapabilityUnsupported as exc:
        job.status = "failed"
        job.error_message = f"{exc.code}: {exc}"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=501, detail=f"text removal unavailable: {exc.code}")

    job.status = "completed"
    job.raw_payload = {
        **(job.raw_payload or {}),
        "output_storage_key": response.output_storage_key,
        "method": response.method,
    }
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return TextRemovalJobCreateOut(job=_serialize(job), region_count=region_count)


@router.get("/jobs/{job_id}", response_model=TextRemovalJobOut)
def get_job(
    project_id: UUID,
    job_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> TextRemovalJobOut:
    job = db.get(TextRemovalJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="job not found")
    return _serialize(job)


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(
    project_id: UUID,
    job_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> None:
    job = db.get(TextRemovalJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="job not found")
    db.delete(job)
    db.commit()
