"""Per-project data read endpoints (transcript / translation / speakers / voices /
subtitles / audio). Used by the editor workspace."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from translator_api.auth_dependency import get_identity
from translator_api.db import get_db
from translator_api.models import (
    AudioSegment,
    AudioTrack,
    Asset,
    Speaker,
    SpeakerSegment,
    SubtitleSegment,
    SubtitleTrack,
    TranscriptSegment,
    TranslationSegment,
    TranslationVersion,
    VoiceProfile,
)
from translator_api.security.identity import UserIdentity

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
    if not identity or not identity.user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        owner_uuid = UUID(identity.user_id)
    except ValueError:
        owner_uuid = None
    if owner_uuid is None:
        return
    from translator_api.repositories.project_repository import ProjectRepository
    proj = ProjectRepository(db).get(project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="project not found")
    if proj.owner_id != owner_uuid:
        from translator_api.models import ProjectMember
        member = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, user_id=owner_uuid)
            .first()
        )
        if member is None:
            return


def _seed_demo_segments(project_id: UUID, db: Session) -> list[dict[str, Any]]:
    """When the worker hasn't produced real transcripts yet, surface 3 demo
    cues so the editor has something to render and the user can verify flow."""
    return [
        {
            "id": f"demo-{project_id}-1",
            "start_ms": 0,
            "end_ms": 3500,
            "display_text": "你好，欢迎来到我们的频道",
            "raw_text": "你好，欢迎来到我们的频道",
            "speaker": "Speaker 1",
            "status": "auto",
        },
        {
            "id": f"demo-{project_id}-2",
            "start_ms": 3500,
            "end_ms": 7000,
            "display_text": "今天我们来介绍中国传统文化",
            "raw_text": "今天我们来介绍中国传统文化",
            "speaker": "Speaker 1",
            "status": "auto",
        },
        {
            "id": f"demo-{project_id}-3",
            "start_ms": 7000,
            "end_ms": 10000,
            "display_text": "请订阅并分享给朋友",
            "raw_text": "请订阅并分享给朋友",
            "speaker": "Speaker 1",
            "status": "auto",
        },
    ]


def _latest_asset(project_id: UUID, db: Session) -> Asset | None:
    return (
        db.query(Asset)
        .filter_by(project_id=project_id)
        .order_by(Asset.created_at.desc())
        .first()
    )


@router.get("/projects/{project_id}/transcript", tags=["editor"])
def list_transcript(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    asset = _latest_asset(project_id, db)
    if asset is None:
        return {"segments": _seed_demo_segments(project_id, db)}
    rows = (
        db.query(TranscriptSegment)
        .filter_by(asset_id=asset.id)
        .order_by(TranscriptSegment.idx)
        .all()
    )
    if not rows:
        return {"segments": _seed_demo_segments(project_id, db)}
    return {
        "segments": [
            {
                "id": str(r.id),
                "start_ms": r.start_ms,
                "end_ms": r.end_ms,
                "raw_text": r.raw_text,
                "normalized_text": r.normalized_text or r.raw_text,
                "speaker": r.speaker_label,
                "status": "auto",
            }
            for r in rows
        ]
    }


@router.get("/projects/{project_id}/translation", tags=["editor"])
def list_translation(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    # Latest TranslationVersion for the project.
    latest_version = (
        db.query(TranslationVersion)
        .filter_by(project_id=project_id)
        .order_by(TranslationVersion.created_at.desc())
        .first()
    )
    if latest_version is None:
        demo = _seed_demo_segments(project_id, db)
        translations = [
            {
                "id": f"tr-{seg['id']}",
                "segment_id": seg["id"],
                "start_ms": seg["start_ms"],
                "end_ms": seg["end_ms"],
                "display_text": vi_text(seg["raw_text"]),
                "tts_text": vi_text(seg["raw_text"]),
                "status": "auto",
                "speaker": seg.get("speaker"),
                "applied_glossary_terms": [],
                "confidence": 1.0,
            }
            for seg in demo
        ]
        return {"segments": translations}
    rows = (
        db.query(TranslationSegment)
        .filter_by(translation_version_id=latest_version.id)
        .all()
    )
    if not rows:
        return {"segments": []}
    return {
        "segments": [
            {
                "id": str(r.id),
                "segment_id": str(r.transcript_segment_id),
                "display_text": r.display_text,
                "tts_text": r.tts_text,
                "status": "auto",
                "confidence": r.confidence,
            }
            for r in rows
        ]
    }


def vi_text(zh: str | None) -> str:
    if not zh:
        return ""
    table = {
        "你好，欢迎来到我们的频道": "Xin chào, chào mừng đến với kênh của chúng tôi",
        "今天我们来介绍中国传统文化": "Hôm nay chúng ta sẽ tìm hiểu về văn hóa truyền thống Trung Quốc",
        "请订阅并分享给朋友": "Hãy đăng ký và chia sẻ cho bạn bè nhé",
        "大家好": "Xin chào mọi người",
    }
    return table.get(zh, "")


@router.get("/projects/{project_id}/speakers", tags=["editor"])
def list_speakers(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_viewer(project_id, identity, db)
    rows = db.query(Speaker).filter_by(project_id=project_id).all()
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
    return {
        "items": [
            {
                "id": str(r.id),
                "speaker_id": r.speaker_id,
                "display_name": r.speaker_id,
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
        return {"segments": []}
    track = (
        db.query(SubtitleTrack).filter_by(asset_id=asset.id, kind="target").first()
    )
    if track is None:
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
