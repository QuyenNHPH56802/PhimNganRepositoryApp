"""OCR region CRUD + run endpoint.

Provides:
- POST /projects/{id}/ocr/run   → run OCR on a frame (or all frames in a range)
- GET  /projects/{id}/ocr/regions → list regions (filter by status)
- PATCH /projects/{id}/ocr/regions/{rid} → edit translation / status
- POST /projects/{id}/ocr/regions/{rid}:approve → convenience action
- DELETE /projects/{id}/ocr/regions/{rid}

Real provider execution is wired into the existing `OcrProvider` hierarchy;
this router focuses on the data lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import OcrRegion, Project

router = APIRouter(prefix="/projects/{project_id}/ocr", tags=["ocr"])

ALLOWED_STATUS = {"pending", "translated", "approved", "rejected"}


# ─── Schemas ─────────────────────────────────────────────────────────────


class OcrRunIn(BaseModel):
    frame_count: int = Field(default=10, ge=1, le=240)
    start_ts_ms: int = Field(default=0, ge=0)
    language_hint: str = Field(default="zh")
    provider_id: str = Field(default="ocr.mock")


class OcrRegionOut(BaseModel):
    id: UUID
    frame_index: int
    frame_ts_ms: int
    bbox: dict
    source_text: str
    translated_text: str | None
    confidence: float | None
    status: str
    provider_id: str | None
    created_at: datetime
    updated_at: datetime


class OcrRegionPatch(BaseModel):
    translated_text: str | None = None
    status: str | None = None


class OcrRunOut(BaseModel):
    project_id: UUID
    frame_count: int
    regions_created: int
    total_regions: int


class OcrRegionListOut(BaseModel):
    regions: list[OcrRegionOut]
    total: int
    by_status: dict[str, int]


# ─── Helpers ─────────────────────────────────────────────────────────────


def _serialize(r: OcrRegion) -> OcrRegionOut:
    return OcrRegionOut(
        id=r.id,
        frame_index=r.frame_index,
        frame_ts_ms=r.frame_ts_ms,
        bbox={"x": r.bbox_x, "y": r.bbox_y, "w": r.bbox_w, "h": r.bbox_h},
        source_text=r.source_text,
        translated_text=r.translated_text,
        confidence=r.confidence,
        status=r.status,
        provider_id=r.provider_id,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.post("/run", response_model=OcrRunOut, status_code=202)
def run_ocr(
    project_id: UUID,
    body: OcrRunIn,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> OcrRunOut:
    """Kick off OCR over `frame_count` evenly-spaced frames.

    The current implementation is synchronous and uses the mock provider;
    a follow-up wires it into the worker queue.
    """
    _ensure_project(db, project_id)

    # Lazy import so missing ML deps don't break import-time.
    from translator_api.providers.ocr.mock_provider import MockOcrProvider
    from translator_api.providers.ocr.base import OcrInput

    # Frame interval: assume 30 fps, one frame per second.
    fps = 30
    frame_step = int(1000 / fps * 30)  # ~1s spacing
    provider = MockOcrProvider()

    created = 0
    now = datetime.now(timezone.utc)
    for i in range(body.frame_count):
        ts = body.start_ts_ms + i * frame_step
        try:
            response = provider.run(
                OcrInput(
                    asset_storage_key=str(project_id),
                    language_hint=body.language_hint,
                    frame_ts_ms=ts,
                ),
                ctx=None,
            )
        except Exception as exc:
            # Skip individual frame errors but log.
            print(f"OCR mock failed for frame {i}: {exc}")
            continue

        for det in response.detections:
            if not det.bbox:
                continue
            box = det.bbox[0]
            region = OcrRegion(
                project_id=project_id,
                frame_index=i,
                frame_ts_ms=ts,
                bbox_x=box.get("x", 0),
                bbox_y=box.get("y", 0),
                bbox_w=box.get("w", 100),
                bbox_h=box.get("h", 30),
                source_text=det.text,
                translated_text=None,
                confidence=det.confidence,
                status="pending",
                provider_id=body.provider_id,
                raw_payload={"detection": {"text": det.text}},
                created_at=now,
                updated_at=now,
            )
            db.add(region)
            created += 1

    db.commit()

    total = db.query(OcrRegion).filter_by(project_id=project_id).count()
    return OcrRunOut(
        project_id=project_id,
        frame_count=body.frame_count,
        regions_created=created,
        total_regions=total,
    )


@router.get("/regions", response_model=OcrRegionListOut)
def list_regions(
    project_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> OcrRegionListOut:
    _ensure_project(db, project_id)

    q = db.query(OcrRegion).filter_by(project_id=project_id)
    if status_filter:
        if status_filter not in ALLOWED_STATUS:
            raise HTTPException(status_code=400, detail=f"invalid status: {status_filter}")
        q = q.filter(OcrRegion.status == status_filter)
    total = q.count()

    rows = q.order_by(OcrRegion.frame_index, OcrRegion.frame_ts_ms).offset(offset).limit(limit).all()

    # Aggregate counts
    by_status: dict[str, int] = {s: 0 for s in ALLOWED_STATUS}
    for s, n in db.query(OcrRegion.status, db.func.count(OcrRegion.id)).filter_by(
        project_id=project_id
    ).group_by(OcrRegion.status):
        by_status[s] = n

    return OcrRegionListOut(
        regions=[_serialize(r) for r in rows],
        total=total,
        by_status=by_status,
    )


@router.patch("/regions/{region_id}", response_model=OcrRegionOut)
def patch_region(
    project_id: UUID,
    region_id: UUID,
    body: OcrRegionPatch,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> OcrRegionOut:
    region = db.get(OcrRegion, region_id)
    if region is None or region.project_id != project_id:
        raise HTTPException(status_code=404, detail="region not found")
    if body.status is not None and body.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail=f"invalid status: {body.status}")
    if body.translated_text is not None:
        region.translated_text = body.translated_text
    if body.status is not None:
        region.status = body.status
    region.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(region)
    return _serialize(region)


@router.post("/regions/{region_id}:approve", response_model=OcrRegionOut)
def approve_region(
    project_id: UUID,
    region_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> OcrRegionOut:
    region = db.get(OcrRegion, region_id)
    if region is None or region.project_id != project_id:
        raise HTTPException(status_code=404, detail="region not found")
    region.status = "approved"
    region.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(region)
    return _serialize(region)


@router.delete("/regions/{region_id}", status_code=204)
def delete_region(
    project_id: UUID,
    region_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> None:
    region = db.get(OcrRegion, region_id)
    if region is None or region.project_id != project_id:
        raise HTTPException(status_code=404, detail="region not found")
    db.delete(region)
    db.commit()
