"""ASR / alignment / diarization activities backed by Phase 2 providers."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from temporalio import activity

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
            transcript_repo.add(response_to_transcript(response, asset.id, session))
            session.commit()
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="align_text")
async def align_text(project_id: str, asset_id: str | None = None) -> dict:
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else asset_repo.list_for_project(UUID(project_id))[0]
        provider = Wav2vec2AlignmentProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        payload = AlignInput(asset_storage_key=asset.storage_key, segments=[])
        response: AlignResponse = await provider.run(payload, ctx=ctx)
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="diarize_segments")
async def diarize_segments(project_id: str, asset_id: str | None = None) -> dict:
    factory = build_factory()
    session = factory()
    try:
        asset_repo = AssetRepository(session)
        asset = asset_repo.get(UUID(asset_id)) if asset_id else asset_repo.list_for_project(UUID(project_id))[0]
        provider = PyannoteDiarizationProvider()
        ctx = ProviderContext(project_id=project_id, asset_id=str(asset.id), db_session=session, storage=build_storage())
        payload = DiarizeInput(asset_storage_key=asset.storage_key)
        response: DiarizeResponse = await provider.run(payload, ctx=ctx)
        return response.model_dump()
    finally:
        session.close()


def response_to_transcript(response: AsrResponse, asset_id: UUID, session) -> "Transcript":  # type: ignore[name-defined]
    from translator_api.models import Transcript, TranscriptSegment, TranscriptWord

    transcript = Transcript(
        asset_id=asset_id,
        language_detected=response.language,
        language_profile="zh-vi",
        model_id=response.model_id,
        signature=response.signature.fingerprint(),
    )
    segments: list[TranscriptSegment] = []
    words: list[TranscriptWord] = []
    for seg in response.segments:
        s = TranscriptSegment(
            transcript_id=transcript.id,
            idx=seg.idx,
            start_ms=seg.start_ms,
            end_ms=seg.end_ms,
            raw_text=seg.text,
        )
        segments.append(s)
    for w in response.words:
        words.append(TranscriptWord(segment_id=transcript.id, idx=w.idx, text=w.text, start_ms=w.start_ms, end_ms=w.end_ms, confidence=w.confidence))
    transcript.segments = segments
    transcript.words = words
    session.flush()
    return transcript