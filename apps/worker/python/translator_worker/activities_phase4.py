"""Phase 4 OCR + text-removal activities."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from temporalio import activity

from translator_api.models import OcrDetection, TextRemovalJob, WorkflowStep
from translator_api.providers.base import ProviderContext
from translator_api.providers.ocr.base import OcrInput
from translator_api.providers.ocr.paddle_provider import PaddleOcrProvider
from translator_api.providers.ocr.base import OcrDetection as ProviderOcrDetection
from translator_api.providers.text_removal.base import TextRemovalInput
from translator_api.providers.text_removal.lama_provider import LamaInpaintProvider
from translator_api.repositories.asset_repository import AssetRepository
from translator_api.repositories.workflow_repository import WorkflowStepRepository
from translator_worker.deps import build_storage, make_worker_session_factory


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _factory():
    return make_worker_session_factory()


def _latest_workflow(session, project_id: UUID):
    from sqlalchemy import select

    from translator_api.models import Workflow

    stmt = select(Workflow).where(Workflow.project_id == project_id).order_by(Workflow.started_at.desc()).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def _record(session, project_id: str, name: str, status: str, signature: str | None = None, message: str | None = None) -> None:
    workflow = _latest_workflow(session, UUID(project_id))
    if workflow is None:
        return
    step = WorkflowStep(
        workflow_id=workflow.id,
        name=name,
        status=status,
        progress_pct=100 if status == "ready" else 0,
        progress_message=message,
        artifact_signature=signature,
        started_at=_now(),
        ended_at=_now() if status in {"ready", "failed"} else None,
    )
    WorkflowStepRepository(session).upsert(step)
    session.commit()


@activity.defn(name="ocr_detect_text")
async def ocr_detect_text(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record(session, project_id, "ocr_detect_text", status="processing")
        asset = AssetRepository(session).get(UUID(asset_id)) if asset_id else AssetRepository(session).list_for_project(UUID(project_id))[0]
        provider = PaddleOcrProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        try:
            response = await provider.run(OcrInput(asset_storage_key=asset.storage_key, language_hint="zh"), ctx=ctx)
        except Exception as exc:
            activity.logger.info("ocr_detect_text stub: %s", exc)
            return {"ok": False, "message": str(exc)}
        for detection in response.detections:
            session.add(
                OcrDetection(
                    asset_id=asset.id,
                    text=detection.text,
                    bbox={"polygon": detection.bbox},
                    frame_ts_ms=detection.frame_ts_ms,
                    confidence=detection.confidence,
                    model_id=response.model_id,
                    language=response.language,
                )
            )
        session.commit()
        _record(session, project_id, "ocr_detect_text", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="text_remove")
async def text_remove(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record(session, project_id, "text_remove", status="processing")
        asset = AssetRepository(session).get(UUID(asset_id)) if asset_id else AssetRepository(session).list_for_project(UUID(project_id))[0]
        rows = session.query(OcrDetection).filter_by(asset_id=asset.id).all()
        detections = [
            ProviderOcrDetection(
                text=row.text,
                bbox=[row.bbox.get("polygon", []) if isinstance(row.bbox, dict) else row.bbox],
                frame_ts_ms=row.frame_ts_ms,
                confidence=row.confidence,
            )
            for row in rows
        ]
        provider = LamaInpaintProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        try:
            response = await provider.run(
                TextRemovalInput(asset_storage_key=asset.storage_key, detections=detections, strategy="inpaint_lama"),
                ctx=ctx,
            )
        except Exception as exc:
            activity.logger.info("text_remove stub: %s", exc)
            return {"ok": False, "message": str(exc)}
        job = TextRemovalJob(
            asset_id=asset.id,
            strategy="inpaint_lama",
            status="ready",
            output_storage_key=response.output_storage_key,
            bbox_payload={"count": len(detections)},
        )
        session.add(job)
        session.commit()
        _record(session, project_id, "text_remove", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()