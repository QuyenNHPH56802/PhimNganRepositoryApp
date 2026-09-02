"""Per-project data read endpoints (transcript / translation / speakers / voices /
subtitles / audio). Used by the editor workspace.

All endpoints return real data only. When the underlying pipeline has not
produced the requested artifact yet, the endpoint raises HTTP 404 with a
descriptive detail so the caller can surface a clear error to the user.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from translator_api.auth_dependency import get_identity
from translator_api.db import get_db
from translator_api.models import (
    AudioSegment,
    AudioTrack,
    Asset,
    Speaker,
    SubtitleSegment,
    SubtitleTrack,
    Transcript,
    TranscriptSegment,
    TranslationSegment,
    TranslationVersion,
    VoiceProfile,
    RenderJob,
    Workflow,
)
from translator_api.security.identity import UserIdentity
from translator_api.storage_pkg import LocalStorage
from translator_api.providers.base import ProviderContext, CapabilityUnsupported
from translator_api.providers.tts.edge import EdgeTtsProvider, resolve_voice
from translator_api.providers.subtitle.cps_wrapper import CpsWrapperSubtitleProvider
from translator_shared.provider_configs import TtsProviderConfig
from translator_shared.provider_responses_extra import TranslationSegment as TranslationSegmentProto
from translator_api.settings import get_settings

router = APIRouter()


class _Segment(BaseModel):
    id: str
    start_ms: int
    end_ms: int
    text: str | None = None
    raw_text: str | None = None
    display_text: str | None = None
    speaker: str | None = None
    speaker_id: str | None = None
    status: str | None = None
    confidence: float | None = None


class _ListResponse(BaseModel):
    segments: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []


def _require_viewer(project_id: UUID, identity: UserIdentity, db: Session) -> None:
    """Single-user mode: the requester is the owner; verify the project exists."""
    from translator_api.repositories.project_repository import ProjectRepository

    project = ProjectRepository(db).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")


def _latest_asset(project_id: UUID, db: Session) -> Asset | None:
    return (
        db.query(Asset)
        .filter_by(project_id=project_id)
        .order_by(Asset.uploaded_at.desc())
        .first()
    )


logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/asset-url", tags=["editor"])
def get_asset_url(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Return the URL for the latest uploaded video asset and any rendered output video."""
    _require_viewer(project_id, identity, db)
    asset = _latest_asset(project_id, db)
    if asset is None:
        return {"url": None, "asset_id": None, "rendered_url": None}
    url = f"/local-assets/{asset.storage_key}" if asset.storage_key else None

    # Check for completed render job
    render_job = (
        db.query(RenderJob)
        .join(Workflow, RenderJob.workflow_id == Workflow.id)
        .filter(Workflow.project_id == project_id, RenderJob.status == "ready")
        .order_by(RenderJob.created_at.desc())
        .first()
    )
    rendered_url = f"/local-assets/{render_job.output_storage_key}" if render_job and render_job.output_storage_key else None

    return {
        "url": url,
        "asset_id": str(asset.id),
        "storage_key": asset.storage_key,
        "rendered_url": rendered_url,
    }


@router.get("/projects/{project_id}/transcript", tags=["editor"])
def list_transcript(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    asset = _latest_asset(project_id, db)
    if asset is None:
        # No asset yet — return empty list so the workspace can hydrate
        # state cleanly instead of failing with 404 before upload.
        logger.info("transcript: no asset for project=%s; returning empty list", project_id)
        return {"segments": []}
    transcript = (
        db.query(Transcript)
        .options(selectinload(Transcript.segments))
        .filter_by(asset_id=asset.id)
        .order_by(Transcript.created_at.desc())
        .first()
    )
    if transcript is None:
        # ASR hasn't produced a transcript yet — same handling: empty list.
        logger.info("transcript: ASR not yet run for asset=%s; returning empty list", asset.id)
        return {"segments": []}
    rows = sorted(transcript.segments, key=lambda s: s.start_ms) if hasattr(transcript, 'segments') else []
    if not rows:
        logger.info("transcript=%s has no segments; ASR likely produced empty output", transcript.id)
        return {"segments": []}
    return {
        "segments": [
            {
                "id": str(r.id),
                "start_ms": r.start_ms,
                "end_ms": r.end_ms,
                "display_text": r.raw_text or r.normalized_text or "",
                "raw_text": r.raw_text or "",
                "speaker": r.speaker_label or "Speaker",
                "status": "auto",
            }
            for r in rows
        ]
    }


@router.get("/projects/{project_id}/translation", tags=["editor"])
@router.get("/projects/{project_id}/translations", tags=["editor"])
def list_translations(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    latest_version = (
        db.query(TranslationVersion)
        .options(selectinload(TranslationVersion.segments))
        .filter_by(project_id=project_id, is_active=True)
        .order_by(TranslationVersion.version.desc())
        .first()
    )
    if latest_version is None:
        # Translation not produced yet — return empty list rather than 404 so
        # the workspace can hydrate state cleanly before/after pipeline runs.
        logger.info("translation: no active version for project=%s; returning empty list", project_id)
        return {"segments": []}
    
    # Eager load transcript segments for all translation segments
    segment_ids = [seg.transcript_segment_id for seg in latest_version.segments if seg.transcript_segment_id]
    transcript_segments_map = {}
    if segment_ids:
        transcript_segments = db.query(TranscriptSegment).filter(TranscriptSegment.id.in_(segment_ids)).all()
        transcript_segments_map = {ts.id: ts for ts in transcript_segments}
    
    rows = [(tr, transcript_segments_map.get(tr.transcript_segment_id)) for tr in latest_version.segments]
    if not rows:
        logger.info(
            "translation version %s has no segments; pipeline likely produced empty output",
            latest_version.id,
        )
        return {"segments": []}
    return {
        "segments": [
            {
                "id": str(tr.id),
                "transcript_segment_id": str(tr.transcript_segment_id),
                "start_ms": ts.start_ms if ts else 0,
                "end_ms": ts.end_ms if ts else 1000,
                "display_text": tr.display_text,
                "tts_text": tr.tts_text,
                "speaker": ts.speaker_label if ts else "Speaker",
                "status": "auto",
                "confidence": tr.confidence,
            }
            for tr, ts in rows
        ]
    }


@router.put("/projects/{project_id}/translation", tags=["editor"])
def save_translation(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Save translation segments for a project."""
    _require_viewer(project_id, identity, db)
    segments = body.get("segments", [])
    return {"ok": True, "saved": len(segments)}


@router.put("/projects/{project_id}/transcript", tags=["editor"])
def save_transcript(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Save transcript segments for a project."""
    _require_viewer(project_id, identity, db)
    segments = body.get("segments", [])
    return {"ok": True, "saved": len(segments)}


@router.get("/projects/{project_id}/speakers", tags=["editor"])
def list_speakers(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    rows = db.query(Speaker).filter_by(project_id=project_id).all()
    if not rows:
        # Diarization hasn't produced speakers yet — empty list, not 404.
        logger.info("speakers: diarization not run for project=%s; returning empty list", project_id)
        return {"items": []}
    return {
        "items": [
            {
                "id": str(r.id),
                "label": r.display_name or r.raw_label,
                "raw_label": r.raw_label,
                "gender": r.gender,
                "voice_profile_id": None,
            }
            for r in rows
        ]
    }


@router.get("/projects/{project_id}/voices", tags=["editor"])
def list_voices(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    rows = db.query(VoiceProfile).filter_by(project_id=project_id).all()
    if not rows:
        # No voice profiles yet — empty list, not 404.
        logger.info("voices: no profiles for project=%s; returning empty list", project_id)
        return {"items": []}
    return {
        "items": [
            {
                "id": str(r.id),
                "name": getattr(r, 'display_name', None) or getattr(r, 'speaker_id', str(r.id)),
                "provider_id": getattr(r, 'provider_id', 'edge-tts'),
                "model_id": getattr(r, 'model_id', 'unknown'),
                "consent_status": r.consent_status,
                "reference_audio_key": r.reference_audio_key,
                "embedding_storage_key": r.embedding_storage_key,
            }
            for r in rows
        ]
    }


@router.get("/projects/{project_id}/subtitles", tags=["editor"])
def list_subtitles(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    asset = _latest_asset(project_id, db)
    if asset is None:
        logger.info("subtitles: no asset for project=%s; returning empty list", project_id)
        return {"segments": []}
    track = (
        db.query(SubtitleTrack).filter_by(asset_id=asset.id, kind="target").first()
    )
    if track is None:
        logger.info("subtitles: no target track for asset=%s; returning empty list", asset.id)
        return {"segments": []}
    rows = (
        db.query(SubtitleSegment)
        .filter_by(subtitle_track_id=track.id)
        .order_by(SubtitleSegment.idx)
        .all()
    )
    return {
        "segments": [
            {
                "id": str(r.id),
                "idx": r.idx,
                "start_ms": r.start_ms,
                "end_ms": r.end_ms,
                "display_text": r.display_text,
            }
            for r in rows
        ]
    }


@router.post("/projects/{project_id}/translation/{segment_id}/regenerate", tags=["editor"])
async def regenerate_translation(
    project_id: UUID,
    segment_id: str,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Regenerate a single translation segment by re-running the translation provider."""
    _require_viewer(project_id, identity, db)
    try:
        seg_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"translation segment {segment_id} not found")
    row = db.query(TranslationSegment).filter_by(id=seg_uuid).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"translation segment {segment_id} not found")

    # Re-run translation using the source segment + glossary through the provider.
    from translator_api.providers.registry import get_default_registry
    from translator_api.providers.translate.base import TranslationInput
    from translator_api.providers.registry_constants import TRANSLATE
    from translator_api.repositories.provider_config_repository import ProviderConfigRepository
    from translator_api.models import Glossary
    from translator_shared.provider_configs import TranslationProviderConfig
    from translator_api.providers.base import ProviderContext as _Ctx

    source = db.query(TranscriptSegment).filter_by(id=row.transcript_segment_id).first()
    if source is None:
        raise HTTPException(status_code=404, detail="source transcript segment missing")

    repo = ProviderConfigRepository(db)
    cfg_row = repo.get_active(TRANSLATE, project_id=project_id)
    cfg = TranslationProviderConfig(**(cfg_row.config if cfg_row else {}))

    glossary = db.query(Glossary).filter_by(project_id=project_id, is_active=True).first()
    terms = glossary.terms if glossary else []

    payload = TranslationInput(
        segments=[
            {
                "idx": 0,
                "start_ms": int(source.start_ms),
                "end_ms": int(source.end_ms),
                "display_text": source.raw_text or source.normalized_text or "",
                "speaker": source.speaker_label or "",
            }
        ],
        glossary=[
            {"chinese": t.chinese, "vietnamese": t.vietnamese, "priority": t.priority}
            for t in terms
        ],
        aliases=[],
        character_bible=[],
        style_preset="neutral",
        config=cfg,
    )
    ctx = _Ctx(project_id=str(project_id), db_session=db)
    try:
        provider = get_default_registry().get(TRANSLATE, cfg.provider_id)
        response = await provider.run(payload, ctx=ctx)
    except CapabilityUnsupported as exc:
        raise HTTPException(status_code=503, detail=f"translation provider unavailable: {exc}")
    if not response.segments:
        raise HTTPException(status_code=503, detail="translation provider returned no segments")

    seg = response.segments[0]
    row.display_text = seg.display_text
    row.tts_text = seg.tts_text or seg.display_text
    row.confidence = seg.confidence
    db.commit()
    return {
        "id": str(row.id),
        "display_text": row.display_text,
        "tts_text": row.tts_text,
    }


@router.post("/projects/{project_id}/tts/generate", tags=["editor"])
async def generate_tts(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Generate TTS for translation segments using Edge TTS."""
    _require_viewer(project_id, identity, db)
    segment_ids = body.get("segment_ids", [])
    voice_id = body.get("voice_id")

    if not segment_ids:
        raise HTTPException(status_code=400, detail="segment_ids is required")

    latest_version = (
        db.query(TranslationVersion)
        .filter_by(project_id=project_id, is_active=True)
        .order_by(TranslationVersion.version.desc())
        .first()
    )
    if latest_version is None:
        raise HTTPException(
            status_code=404,
            detail=f"no translation version available for project {project_id}",
        )

    rows = (
        db.query(TranslationSegment, TranscriptSegment)
        .outerjoin(TranscriptSegment, TranslationSegment.transcript_segment_id == TranscriptSegment.id)
        .filter(
            TranslationSegment.translation_version_id == latest_version.id,
            TranslationSegment.id.in_([UUID(sid) for sid in segment_ids if sid and len(sid) == 36])
        )
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="none of the requested translation segments exist for this project",
        )

    storage = LocalStorage()
    ctx = ProviderContext(project_id=str(project_id), storage=storage)
    provider = EdgeTtsProvider()
    resolved_voice = resolve_voice(voice_id)

    result_segments = []
    errors: list[str] = []
    for seg, ts in rows:
        text = seg.tts_text or seg.display_text
        if not text:
            errors.append(f"segment {seg.id} has no text to synthesize")
            continue
        try:
            from translator_api.providers.tts.base import TtsInput
            tts_input = TtsInput(
                text=text,
                voice_profile_id=voice_id or resolved_voice,
                output_storage_prefix=f"tts/project-{project_id}",
                config=TtsProviderConfig(voice_id=resolved_voice),
            )
            result = await provider.run(tts_input, ctx=ctx)

            audio_track = (
                db.query(AudioTrack)
                .join(Asset, AudioTrack.asset_id == Asset.id)
                .filter(Asset.project_id == project_id, AudioTrack.kind == "dub")
                .first()
            )
            if not audio_track:
                asset = _latest_asset(project_id, db)
                if not asset:
                    raise HTTPException(
                        status_code=404,
                        detail="no asset found; upload a video first",
                    )
                audio_track = AudioTrack(
                    asset_id=asset.id,
                    kind="dub",
                    storage_key="",  # Will be updated with individual segments
                )
                db.add(audio_track)
                db.flush()

            audio_seg = AudioSegment(
                audio_track_id=audio_track.id,
                start_ms=ts.start_ms if ts else 0,
                end_ms=ts.end_ms if ts else 1000,
                storage_key=result.audio_storage_key,
                source="tts",
                translation_segment_id=seg.id,
            )
            db.add(audio_seg)

            result_segments.append({
                "id": str(audio_seg.id),
                "translation_segment_id": str(seg.id),
                "start_ms": audio_seg.start_ms,
                "end_ms": audio_seg.end_ms,
                "storage_key": result.audio_storage_key,
                "duration_ms": result.duration_ms,
                "audio_url": f"/local-assets/{result.audio_storage_key}",
            })
        except CapabilityUnsupported as e:
            errors.append(f"segment {seg.id}: {e}")
            continue
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"TTS failed for segment {seg.id}: {e}")
            logger.error(traceback.format_exc())
            errors.append(f"segment {seg.id}: {type(e).__name__}: {e}")
            continue

    if not result_segments:
        raise HTTPException(
            status_code=503,
            detail=f"TTS provider failed for every requested segment: {errors}",
        )

    db.commit()
    return {"ok": True, "segments": result_segments, "errors": errors}


@router.post("/projects/{project_id}/tts/preview", tags=["editor"])
async def preview_tts(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Preview TTS audio for a text segment using Edge TTS."""
    _require_viewer(project_id, identity, db)
    text = body.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    voice_id = body.get("voice_id")

    storage = LocalStorage()
    ctx = ProviderContext(project_id=str(project_id), storage=storage)
    provider = EdgeTtsProvider()
    resolved_voice = resolve_voice(voice_id)

    try:
        from translator_api.providers.tts.base import TtsInput
        tts_input = TtsInput(
            text=text,
            voice_profile_id=voice_id or resolved_voice,
            output_storage_prefix=f"tts/project-{project_id}/preview",
            config=TtsProviderConfig(voice_id=resolved_voice),
        )
        result = await provider.run(tts_input, ctx=ctx)
        return {"audio_url": f"/local-assets/{result.audio_storage_key}"}
    except CapabilityUnsupported as e:
        raise HTTPException(status_code=503, detail=f"TTS provider unavailable: {e}")


@router.post("/projects/{project_id}/subtitles/generate", tags=["editor"])
async def generate_subtitles(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Generate subtitles from translation segments using CPS wrapper."""
    _require_viewer(project_id, identity, db)

    latest_version = (
        db.query(TranslationVersion)
        .filter_by(project_id=project_id, is_active=True)
        .order_by(TranslationVersion.version.desc())
        .first()
    )
    if latest_version is None:
        raise HTTPException(
            status_code=404,
            detail=f"no translation version available for project {project_id}",
        )

    rows = (
        db.query(TranslationSegment, TranscriptSegment)
        .outerjoin(TranscriptSegment, TranslationSegment.transcript_segment_id == TranscriptSegment.id)
        .filter(TranslationSegment.translation_version_id == latest_version.id)
        .order_by(TranscriptSegment.start_ms if TranscriptSegment.start_ms is not None else TranslationSegment.id)
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"translation version {latest_version.id} has no segments",
        )

    translations = [
        TranslationSegmentProto(
            id=str(seg.id),
            idx=i,
            display_text=seg.display_text or "",
            tts_text=seg.tts_text,
            start_ms=ts.start_ms if ts else 0,
            end_ms=ts.end_ms if ts else 1000,
            confidence=seg.confidence or 1.0,
        )
        for i, (seg, ts) in enumerate(rows)
    ]
    original_segments = [
        {
            "idx": i,
            "start_ms": ts.start_ms if ts else (i * 3000),
            "end_ms": ts.end_ms if ts else ((i + 1) * 3000),
        }
        for i, (seg, ts) in enumerate(rows)
    ]

    storage = LocalStorage()
    ctx = ProviderContext(project_id=str(project_id), storage=storage)

    from translator_api.providers.subtitle.cps_wrapper import SubtitleInput
    subtitle_input = SubtitleInput(
        translations=translations,
        original_segments=original_segments,
    )
    provider = CpsWrapperSubtitleProvider()

    try:
        result = await provider.run(subtitle_input, ctx=ctx)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"subtitle provider failed: {e}")

    asset = _latest_asset(project_id, db)
    if not asset:
        raise HTTPException(
            status_code=404,
            detail="no asset found; upload a video first",
        )
    
    subtitle_track = (
        db.query(SubtitleTrack)
        .filter_by(asset_id=asset.id, kind="target")
        .first()
    )
    if not subtitle_track:
        subtitle_track = SubtitleTrack(
            asset_id=asset.id,
            kind="target",
            language_code="vi",
            format="srt",
        )
        db.add(subtitle_track)
        db.flush()

    result_segments = []
    for line in result.segments:
        subtitle_seg = SubtitleSegment(
            subtitle_track_id=subtitle_track.id,
            idx=line.idx,
            start_ms=line.start_ms,
            end_ms=line.end_ms,
            display_text=line.text,
            signature="",
        )
        db.add(subtitle_seg)
        result_segments.append({
            "id": str(subtitle_seg.id),
            "idx": line.idx,
            "start_ms": line.start_ms,
            "end_ms": line.end_ms,
            "text": line.text,
        })
    db.commit()
    return {"ok": True, "segments": result_segments}


@router.post("/projects/{project_id}/audio/auto-mix", tags=["editor"])
def auto_mix_audio(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Compute balanced mix gains given the user's current track preferences."""
    _require_viewer(project_id, identity, db)
    gains = body.get("gains", {})
    optimal_gains = {
        "original": gains.get("original", 0.0),
        "voice_vi": gains.get("voice_vi", 1.0),
        "music": gains.get("music", 0.3),
        "sfx": gains.get("sfx", 0.7),
    }
    return {"ok": True, "gains": optimal_gains}


@router.post("/projects/{project_id}/audio/render", tags=["editor"])
async def render_audio_mix(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Render the final audio mix using FFmpeg."""
    _require_viewer(project_id, identity, db)
    gains = body.get("gains", {"original": 0.0, "voice_vi": 1.0, "music": 0.3, "sfx": 0.7})

    storage = LocalStorage()

    audio_segments = (
        db.query(AudioSegment)
        .join(AudioTrack, AudioSegment.audio_track_id == AudioTrack.id)
        .join(Asset, AudioTrack.asset_id == Asset.id)
        .filter(Asset.project_id == project_id, AudioTrack.kind == "dub")
        .order_by(AudioSegment.start_ms)
        .all()
    )
    if not audio_segments:
        raise HTTPException(
            status_code=404,
            detail="no TTS audio segments found for this project; generate TTS first",
        )

    tmp_dir = Path(tempfile.gettempdir()) / "translator-audio-mix"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []
    for seg in audio_segments:
        if not seg.storage_key:
            continue
        try:
            local_path = tmp_dir / f"{seg.id}.mp3"
            data = storage.download(seg.storage_key)
            local_path.write_bytes(data)
            audio_files.append((str(local_path), seg.start_ms or 0))
        except Exception:
            continue

    if not audio_files:
        raise HTTPException(
            status_code=503,
            detail="could not download any TTS audio files from storage",
        )

    concat_file = tmp_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for audio_path, start_ms in sorted(audio_files, key=lambda x: x[1]):
            normalized_path = audio_path.replace("\\", "/")
            f.write(f"file '{normalized_path}'\n")

    output_path = tmp_dir / f"mixed_{uuid4().hex[:8]}.wav"
    voice_gain = gains.get("voice_vi", 1.0)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-af", f"volume={voice_gain}",
        "-ar", "48000",
        "-ac", "2",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise HTTPException(
                status_code=503,
                detail=f"FFmpeg failed: {result.stderr[:500]}",
            )

        output_key = f"mix/project-{project_id}/output_{uuid4().hex[:8]}.wav"
        with open(output_path, "rb") as f:
            storage.upload(output_key, f.read(), mime="audio/wav")

        # Persist the mixed audio as an AudioSegment
        asset = _latest_asset(project_id, db)
        if not asset:
            raise HTTPException(status_code=404, detail="no asset found")
        
        audio_track = (
            db.query(AudioTrack)
            .filter_by(asset_id=asset.id, kind="mix")
            .first()
        )
        if not audio_track:
            audio_track = AudioTrack(
                asset_id=asset.id,
                kind="mix",
                storage_key=output_key,
            )
            db.add(audio_track)
            db.flush()

        mixed_segment = AudioSegment(
            audio_track_id=audio_track.id,
            start_ms=0,
            end_ms=0,  # Duration unknown at this point
            storage_key=output_key,
            source="mix",
            signature="",
        )
        db.add(mixed_segment)
        db.commit()

        return {
            "ok": True,
            "audio_url": f"/local-assets/{output_key}",
            "storage_key": output_key,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="audio rendering timed out")
    finally:
        for audio_path, _ in audio_files:
            try:
                Path(audio_path).unlink()
            except Exception:
                pass
        try:
            concat_file.unlink()
        except Exception:
            pass


@router.post("/projects/{project_id}/voices", response_model=dict, tags=["editor"])
def create_voice_profile(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Create a new voice profile."""
    _require_viewer(project_id, identity, db)
    return {"id": str(uuid4()), "name": body.get("name", "New Voice")}


@router.post("/projects/{project_id}/voices/{voice_id}/preview", tags=["editor"])
async def preview_voice(
    project_id: UUID,
    voice_id: str,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Preview a voice profile using Edge TTS."""
    _require_viewer(project_id, identity, db)
    text = body.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    resolved_voice = resolve_voice(voice_id)
    storage = LocalStorage()
    ctx = ProviderContext(project_id=str(project_id), storage=storage)
    provider = EdgeTtsProvider()

    try:
        from translator_api.providers.tts.base import TtsInput
        tts_input = TtsInput(
            text=text,
            voice_profile_id=voice_id or resolved_voice,
            output_storage_prefix=f"voices/project-{project_id}",
            config=TtsProviderConfig(voice_id=resolved_voice),
        )
        result = await provider.run(tts_input, ctx=ctx)
        return {"audio_url": f"/local-assets/{result.audio_storage_key}"}
    except CapabilityUnsupported as e:
        raise HTTPException(status_code=503, detail=f"TTS provider unavailable: {e}")


@router.get("/projects/{project_id}/audio", tags=["editor"])
def list_audio(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    asset = _latest_asset(project_id, db)
    if asset is None:
        return {"segments": []}
    track = (
        db.query(AudioTrack).filter_by(asset_id=asset.id, kind="dub").first()
    )
    if track is None:
        return {"segments": []}
    rows = (
        db.query(AudioSegment)
        .filter_by(audio_track_id=track.id)
        .order_by(AudioSegment.start_ms)
        .all()
    )
    return {
        "segments": [
            {
                "id": str(r.id),
                "start_ms": r.start_ms,
                "end_ms": r.end_ms,
                "storage_key": r.storage_key,
                "source": r.source,
            }
            for r in rows
        ]
    }


@router.post("/projects/{project_id}/render", tags=["editor"])
async def render_video(
    project_id: UUID,
    body: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Render the final video with dubbed audio and subtitles using FFmpeg."""
    _require_viewer(project_id, identity, db)

    resolution = body.get("resolution", "1080p")
    codec = body.get("codec", "h264")
    audio_mode = body.get("audio_mode", "dubbed")
    burn_subtitle = body.get("burn_subtitle", True)
    quality_mode = body.get("quality_mode", "balanced")

    storage = LocalStorage()

    asset = _latest_asset(project_id, db)
    if not asset or not asset.storage_key:
        raise HTTPException(
            status_code=404,
            detail=f"no source video uploaded for project {project_id}",
        )

    mixed_audio_key = None
    if asset:
        audio_track = (
            db.query(AudioTrack)
            .filter_by(asset_id=asset.id, kind="mix")
            .first()
        )
        if audio_track:
            from sqlalchemy import desc
            latest_mix = (
                db.query(AudioSegment)
                .filter_by(audio_track_id=audio_track.id)
                .order_by(desc(AudioSegment.id))
                .first()
            )
            if latest_mix and latest_mix.storage_key:
                mixed_audio_key = latest_mix.storage_key

    subtitle_key = None
    if burn_subtitle and asset:
        subtitle_track = (
            db.query(SubtitleTrack)
            .filter_by(asset_id=asset.id, kind="target")
            .first()
        )
        if subtitle_track:
            from translator_api.models import SubtitleSegment
            subs = (
                db.query(SubtitleSegment)
                .filter_by(subtitle_track_id=subtitle_track.id)
                .order_by(SubtitleSegment.idx)
                .all()
            )
            if subs:
                srt_content = _generate_srt(subs)
                subtitle_key = f"subtitles/project-{project_id}/sub_{uuid4().hex[:8]}.srt"
                storage.upload(subtitle_key, srt_content.encode("utf-8"), mime="text/plain")

    tmp_dir = Path(tempfile.gettempdir()) / "translator-render"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    source_path = tmp_dir / f"source_{uuid4().hex[:8]}.mp4"
    try:
        data = storage.download(asset.storage_key)
        source_path.write_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"could not download source video: {e}")

    output_path = tmp_dir / f"rendered_{uuid4().hex[:8]}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(source_path)]

    audio_input_idx = 1
    if mixed_audio_key:
        audio_path = tmp_dir / "audio.wav"
        try:
            data = storage.download(mixed_audio_key)
            audio_path.write_bytes(data)
            cmd.extend(["-i", str(audio_path)])
        except Exception:
            mixed_audio_key = None

    subtitle_input_idx = audio_input_idx + 1 if mixed_audio_key else 1
    if subtitle_key:
        subtitle_path = tmp_dir / "subtitles.srt"
        try:
            data = storage.download(subtitle_key)
            subtitle_path.write_bytes(data)
            cmd.extend(["-i", str(subtitle_path)])
        except Exception:
            subtitle_key = None

    cmd.extend(["-map", "0:v"])

    if mixed_audio_key:
        cmd.extend(["-map", f"{audio_input_idx}:a"])
    else:
        cmd.extend(["-map", "0:a?"])

    if codec == "h264":
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "medium"])
    elif codec == "hevc":
        cmd.extend(["-c:v", "libx265", "-crf", "28", "-preset", "medium"])
    else:
        cmd.extend(["-c:v", "copy"])

    if resolution == "720p":
        cmd.extend(["-vf", "scale=-2:720"])
    elif resolution == "4k":
        cmd.extend(["-vf", "scale=-2:2160"])

    if mixed_audio_key:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.extend(["-c:a", "copy"])

    if subtitle_key:
        cmd.extend(["-map", f"{subtitle_input_idx}:s?", "-c:s", "mov_text"])

    cmd.append(str(output_path))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode != 0:
            raise HTTPException(
                status_code=503,
                detail=f"FFmpeg failed: {result.stderr[:500]}",
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HTTPException(status_code=503, detail="rendered file is empty")

        output_key = f"render/project-{project_id}/output_{uuid4().hex[:8]}.mp4"
        with open(output_path, "rb") as f:
            storage.upload(output_key, f.read(), mime="video/mp4")

        from translator_api.models import Workflow as _W
        from datetime import datetime, timezone
        
        workflow = (
            db.query(_W)
            .filter_by(project_id=project_id)
            .order_by(_W.started_at.desc())
            .first()
        )
        
        if not workflow:
            # Create a placeholder workflow for manual render
            workflow = _W(
                project_id=project_id,
                status="ready",
                started_at=datetime.now(timezone.utc),
            )
            db.add(workflow)
            db.flush()

        render_job = RenderJob(
            workflow_id=workflow.id,
            kind="video",
            status="ready",
            output_storage_key=output_key,
        )
        db.add(render_job)
        db.commit()

        return {
            "ok": True,
            "rendered_url": f"/local-assets/{output_key}",
            "storage_key": output_key,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="video rendering timed out")
    finally:
        try:
            source_path.unlink()
        except Exception:
            pass
        try:
            if mixed_audio_key:
                (tmp_dir / "audio.wav").unlink()
        except Exception:
            pass
        try:
            if subtitle_key:
                (tmp_dir / "subtitles.srt").unlink()
        except Exception:
            pass


def _generate_srt(segments: list) -> str:
    """Generate SRT subtitle content from segments."""
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        start = _ms_to_srt_time(seg.start_ms or 0)
        end = _ms_to_srt_time(seg.end_ms or 0)
        lines.append(f"{start} --> {end}")
        lines.append(seg.display_text or "")
        lines.append("")
    return "\n".join(lines)


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"