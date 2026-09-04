"""Phase 7 voice cloning pipeline activities."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from temporalio import activity

from translator_api.models import AuditLog, VoiceProfile
from translator_api.providers.base import ConsentMissing
from translator_api.providers.voice_clone.cosyvoice import CosyVoice3VoiceCloneProvider  # noqa: F401
from translator_api.providers.voice_clone.vieneu import VieNeuVoiceCloneProvider
from translator_api.providers.voice_clone.base import VoiceCloneInput
from translator_api.repositories.workflow_repository import WorkflowStepRepository
from translator_worker.deps import build_storage, make_worker_session_factory


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _latest_workflow(session, project_id: UUID):
    from translator_api.models import Workflow

    stmt = select(Workflow).where(Workflow.project_id == project_id).order_by(Workflow.started_at.desc()).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def _record(session, project_id: str, name: str, status: str, message: str | None = None) -> None:
    workflow = _latest_workflow(session, UUID(project_id))
    if workflow is None:
        return
    WorkflowStepRepository(session).upsert(
        type("Step", (), {
            "workflow_id": workflow.id,
            "name": name,
            "status": status,
            "progress_pct": 100 if status == "ready" else 0,
            "progress_message": message,
            "artifact_signature": None,
            "started_at": _now(),
            "ended_at": _now() if status in {"ready", "failed"} else None,
        })()
    )
    session.commit()


@activity.defn(name="voice_extract_embedding")
async def voice_extract_embedding(speaker_id: str, audio_key: str) -> dict:
    factory = make_worker_session_factory()
    session = factory()
    try:
        profile = session.get(VoiceProfile, UUID(speaker_id))
        if profile is None:
            raise activity.ActivityFailure(f"voice profile {speaker_id} not found")
        if profile.consent_status != "granted":
            raise activity.ActivityFailure(f"voice consent status is {profile.consent_status}")
        key = f"voice_embeddings/{speaker_id}/{os.urandom(8).hex()}.bin"
        build_storage().upload(key, b"")
        session.add(AuditLog(entity_type="voice_profile", entity_id=speaker_id, action="embedding_extracted", payload={"audio_key": audio_key, "embedding_key": key}))
        session.commit()
        return {"speaker_id": speaker_id, "embedding_key": key, "embedding_dim": 256, "sample_rate": 16000, "model_id": "stub"}
    finally:
        session.close()


@activity.defn(name="voice_clone_synthesize")
async def voice_clone_synthesize(speaker_id: str, text: str, output_key_hint: str | None = None) -> dict:
    factory = make_worker_session_factory()
    session = factory()
    try:
        profile = session.get(VoiceProfile, UUID(speaker_id))
        if profile is None or profile.consent_status != "granted":
            raise ConsentMissing("consent-required", "voice profile missing or not granted")
        provider = VieNeuVoiceCloneProvider()
        embedding_key = profile.reference_audio_key or "voice_embeddings/stub.bin"
        from translator_api.providers.base import ProviderContext

        ctx = ProviderContext(project_id=profile.project_id, asset_id=None, db_session=session, storage=build_storage(), voice_consent=profile.consent_status)
        try:
            response = await provider.synthesize(VoiceCloneInput(text=text, embedding_storage_key=embedding_key, speaker_id=speaker_id, output_storage_prefix="voice_clone"), ctx=ctx)
        except ConsentMissing:
            raise
        except Exception as exc:
            activity.logger.info("voice_clone_synthesize stub: %s", exc)
            return {"ok": False, "message": str(exc)}
        session.add(AuditLog(entity_type="voice_profile", entity_id=speaker_id, action="clone_synthesized", payload={"text_length": len(text), "output_key": response.output_storage_key}))
        session.commit()
        return response.model_dump()
    finally:
        session.close()
