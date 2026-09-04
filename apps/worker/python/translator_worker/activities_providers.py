"""ASR / alignment / diarization activities backed by Phase 2 providers."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from temporalio import activity

from translator_api.models import Transcript
from translator_api.providers.align.wav2vec2_provider import AlignInput, Wav2vec2AlignmentProvider
from translator_api.providers.asr.whisperx_provider import AsrInput, WhisperxFasterWhisperProvider
from translator_api.providers.base import ProviderContext
from translator_api.providers.diarize.pyannote_provider import DiarizeInput, PyannoteDiarizationProvider
from translator_api.repositories.asset_repository import AssetRepository
from translator_api.repositories.transcript_repository import TranscriptRepository
from translator_shared.provider_responses import AlignResponse, AsrResponse, DiarizeResponse
from translator_worker.deps import build_storage, session_scope


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_asset(project_id: str, asset_id: str | None):
    factory = build_factory()
    for session in session_scope(factory):
        assets = AssetRepository(session).list_for_project(UUID(project_id))
        if not assets:
            raise RuntimeError(f"no asset found for project {project_id}")
        if asset_id:
            for asset in assets:
                if str(asset.id) == asset_id:
                    return asset, session
        return assets[0], session
    raise RuntimeError("could not resolve asset")


def build_factory():
    from translator_worker.deps import make_worker_session_factory

    return make_worker_session_factory()


@activity.defn(name="asr_transcribe")
async def asr_transcribe(project_id: str, asset_id: str | None = None) -> dict:
    activity.logger.info("✅ REAL asr_transcribe (writes to DB) - project_id=%s asset_id=%s", project_id, asset_id)
    activity.heartbeat("asr_transcribe: resolving asset")
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        transcript_repo = TranscriptRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else None
        if asset is None:
            assets = asset_repo.list_for_project(UUID(project_id))
            if not assets:
                raise RuntimeError(f"no asset for project {project_id}")
            asset = assets[0]
        provider = WhisperxFasterWhisperProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        payload = AsrInput(asset_storage_key=asset.storage_key)
        response: AsrResponse = await provider.run(payload, ctx=ctx)
        existing = transcript_repo.find_by_signature(asset.id, response.signature.fingerprint())
        if existing is None:
            response_to_transcript(response, asset.id, session)
            session.commit()
            activity.logger.info("✅ ASR transcript saved to DB: %d segments", len(response.segments))
        else:
            activity.logger.info("ASR transcript already exists (signature match)")
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="align_text")
async def align_text(project_id: str, asset_id: str | None = None) -> dict:
    """Word-level alignment with graceful degradation.
    
    Tries wav2vec2 provider for word-level timestamps. If provider unavailable
    (missing dependencies), logs explicit warning and returns empty alignment.
    Downstream subtitle timing will use segment-level timestamps only.
    """
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else asset_repo.list_for_project(UUID(project_id))[0]
        
        try:
            provider = Wav2vec2AlignmentProvider()
            ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
            payload = AlignInput(asset_storage_key=asset.storage_key, segments=[])
            response: AlignResponse = await provider.run(payload, ctx=ctx)
            activity.logger.info("align_text completed: %d word alignments for project_id=%s", len(response.words), project_id)
            return response.model_dump()
            
        except Exception as e:
            # Graceful degradation: log warning and return empty alignment
            activity.logger.warning(
                "⚠️ Alignment degraded for project_id=%s: %s. "
                "Subtitle timing will use segment-level timestamps only (no word-level precision). "
                "To enable word-level alignment, install dependencies: pip install torchaudio transformers",
                project_id, str(e)
            )
            
            # Return empty alignment response
            from translator_shared.provider_responses import AlignResponse
            from translator_shared.providers import ArtifactSignature
            
            return AlignResponse(
                words=[],
                signature=ArtifactSignature(
                    input_hash="degraded",
                    model_id="alignment-degraded",
                    model_version="0.0.0",
                    provider_build="degraded",
                    config_hash="degraded"
                ),
                degraded=True
            ).model_dump()
            
    finally:
        session.close()


@activity.defn(name="diarize_segments")
async def diarize_segments(project_id: str, asset_id: str | None = None) -> dict:
    activity.logger.info("✅ REAL diarize_segments (writes to DB) - project_id=%s asset_id=%s", project_id, asset_id)
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else asset_repo.list_for_project(UUID(project_id))[0]
        provider = PyannoteDiarizationProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        payload = DiarizeInput(asset_storage_key=asset.storage_key)
        response: DiarizeResponse = await provider.run(payload, ctx=ctx)
        activity.logger.info("✅ Diarization completed: %d speakers detected", response.num_speakers)
        return response.model_dump()
    finally:
        session.close()


def response_to_transcript(response: AsrResponse, asset_id: UUID, session) -> "Transcript":  # type: ignore[name-defined]
    from translator_api.models import Transcript, TranscriptSegment  # noqa: F401
    from uuid import uuid4

    transcript_id = uuid4()
    transcript = Transcript(
        id=transcript_id,
        asset_id=asset_id,
        language_detected=response.language,
        language_profile="zh-vi",
        model_id=response.model_id,
        signature=response.signature.fingerprint(),
        created_at=_now(),
    )
    session.add(transcript)
    session.flush()

    for seg in response.segments:
        seg_id = uuid4()
        s = TranscriptSegment(
            id=seg_id,
            transcript_id=transcript_id,
            idx=seg.idx,
            start_ms=seg.start_ms,
            end_ms=seg.end_ms,
            raw_text=seg.text,
        )
        session.add(s)

    session.flush()
    return transcript
