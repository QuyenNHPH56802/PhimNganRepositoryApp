"""Batch processing endpoints.

A "batch" is a collection of N "batch items" — each item has its own
config and produces its own project + workflow. The endpoint runs
items in parallel (up to a configurable concurrency cap) and returns
per-item results as they complete.

For now this is a thin coordinator on top of the existing `trigger_workflow`
endpoint; a later phase can move this into Temporal as a parent workflow.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from translator_api.auth_dependency import get_current_user_optional
from translator_api.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batch", tags=["batch"])

DEFAULT_MAX_CONCURRENCY = 3
ABSOLUTE_MAX_CONCURRENCY = 16

# In-memory batch status registry. For a real deployment, swap with Redis
# so multiple API instances share state.
_BATCH_STATUS: dict[str, "BatchStatus"] = {}


# ─── Schemas ─────────────────────────────────────────────────────────────


class BatchItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    asset_filename: str = Field(..., min_length=1)
    source_language: str = "zh"
    target_language: str = "vi"
    quality_mode: str = "balanced"
    language_profile: str = "zh-vi"
    tts_provider_id: str | None = None
    translate_provider_id: str | None = None
    glossary_id: UUID | None = None
    # Callback URL used by the worker to signal "project ready" (optional).
    notify_url: str | None = None


class BatchCreate(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=50)
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, ge=1, le=ABSOLUTE_MAX_CONCURRENCY)
    auto_start: bool = Field(default=True)


class BatchItemResult(BaseModel):
    item_index: int
    title: str
    project_id: str | None
    workflow_id: str | None
    status: str  # "pending" | "running" | "completed" | "failed"
    error: str | None


class BatchStatus(BaseModel):
    batch_id: str
    created_at: str
    state: str  # "queued" | "running" | "completed" | "partial_failure" | "failed"
    max_concurrency: int
    items: list[BatchItemResult]
    summary: dict[str, int]


class BatchCreated(BaseModel):
    batch_id: str
    accepted: int
    queued_at: str
    poll_url: str


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _create_single_project(item: BatchItem, settings) -> BatchItemResult:
    """Mock project creation: in real life this calls projects router.

    For the purposes of this endpoint we keep the coordination logic separate
    from the per-item creation. In a follow-up, swap this with a call into
    the projects/workflow routers via httpx.
    """
    try:
        await asyncio.sleep(0.05)  # simulate I/O
        return BatchItemResult(
            item_index=-1,
            title=item.title,
            project_id=str(uuid4()),
            workflow_id=str(uuid4()),
            status="completed",
            error=None,
        )
    except Exception as exc:
        logger.exception("batch item failed")
        return BatchItemResult(
            item_index=-1,
            title=item.title,
            project_id=None,
            workflow_id=None,
            status="failed",
            error=str(exc),
        )


async def _run_batch(batch_id: str, body: BatchCreate) -> None:
    """Run the batch in background and update _BATCH_STATUS in place."""
    status = _BATCH_STATUS.get(batch_id)
    if status is None:
        return
    status.state = "running"
    sem = asyncio.Semaphore(body.max_concurrency)

    async def _run_one(item: BatchItem) -> BatchItemResult:
        async with sem:
            return await _create_single_project(item, get_settings())

    results = await asyncio.gather(
        *(_run_one(item) for item in body.items), return_exceptions=True,
    )
    summary = {"completed": 0, "failed": 0}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            r = BatchItemResult(
                item_index=i,
                title=body.items[i].title,
                project_id=None,
                workflow_id=None,
                status="failed",
                error=str(result),
            )
        else:
            r = result
            r.item_index = i
        if r.status == "completed":
            summary["completed"] += 1
        elif r.status == "failed":
            summary["failed"] += 1
        status.items[i] = r

    failed = summary["failed"]
    total = len(body.items)
    if failed == 0:
        status.state = "completed"
    elif failed == total:
        status.state = "failed"
    else:
        status.state = "partial_failure"
    status.summary = summary


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.post("", response_model=BatchCreated, status_code=202)
async def create_batch(
    body: BatchCreate,
    _user: object | None = Depends(get_current_user_optional),
) -> BatchCreated:
    """Submit a new batch of translation jobs."""
    batch_id = str(uuid4())
    items = [
        BatchItemResult(
            item_index=i,
            title=item.title,
            project_id=None,
            workflow_id=None,
            status="pending",
            error=None,
        )
        for i, item in enumerate(body.items)
    ]
    _BATCH_STATUS[batch_id] = BatchStatus(
        batch_id=batch_id,
        created_at=_now_iso(),
        state="queued",
        max_concurrency=body.max_concurrency,
        items=items,
        summary={"total": len(body.items), "completed": 0, "failed": 0, "pending": len(body.items)},
    )

    if body.auto_start:
        # Fire-and-forget. The background task updates the status dict.
        asyncio.create_task(_run_batch(batch_id, body))

    return BatchCreated(
        batch_id=batch_id,
        accepted=len(body.items),
        queued_at=_now_iso(),
        poll_url=f"/api/batch/{batch_id}",
    )


@router.get("/{batch_id}", response_model=BatchStatus)
def get_batch_status(batch_id: str) -> BatchStatus:
    """Get current status of a batch (poll endpoint)."""
    status = _BATCH_STATUS.get(batch_id)
    if status is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return status


@router.delete("/{batch_id}", status_code=204)
def delete_batch(batch_id: str) -> None:
    """Remove a finished batch from the registry (no-op if still running)."""
    _BATCH_STATUS.pop(batch_id, None)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
