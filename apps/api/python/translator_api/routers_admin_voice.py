"""Voice admin endpoints (Phase 8).

Endpoints:
  GET  /admin/voice-profiles
  POST /admin/voice-profiles
  PUT  /admin/voice-profiles/{id}

State machine for `consent_status`:
  pending  -> granted   (requires evidence_storage_key)
  pending  -> revoked
  granted  -> revoked
  revoked  -> granted   (requires evidence_storage_key)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.auth import UserIdentity
from translator_api.dependencies import get_db, get_identity
from translator_api.models import AuditLog, VoiceProfile


router = APIRouter(prefix="/admin/voice-profiles", tags=["admin-voice"])


CONSET_STATE_MACHINE: dict[str, set[str]] = {
    "pending": {"granted", "revoked"},
    "granted": {"revoked"},
    "revoked": {"granted"},
}


class VoiceProfileCreate(BaseModel):
    project_id: UUID
    speaker_id: str = Field(min_length=1, max_length=128)
    reference_audio_key: str | None = None
    consent_status: str = Field(pattern="^(pending|granted|revoked)$")
    consent_evidence_key: str | None = None


class VoiceProfileUpdate(BaseModel):
    consent_status: str = Field(pattern="^(pending|granted|revoked)$")
    consent_evidence_key: str | None = None
    reference_audio_key: str | None = None


class VoiceProfileResponse(BaseModel):
    id: UUID
    project_id: UUID
    speaker_id: str
    consent_status: str
    reference_audio_key: str | None
    consent_evidence_key: str | None
    embedding_storage_key: str | None
    created_at: datetime
    updated_at: datetime


def _require_admin(identity: UserIdentity, db: Session) -> None:
    from translator_api.models import User

    user = db.get(User, UUID(identity.user_id))
    if user is None or not user.is_admin:
        raise HTTPException(status_code=403, detail="admin role required")


def _ensure_transition(current: str, new: str) -> None:
    if new not in CONSET_STATE_MACHINE.get(current, set()):
        raise HTTPException(
            status_code=409,
            detail=f"invalid consent transition {current} -> {new}",
        )


def _ensure_evidence(consent_status: str, evidence_key: str | None) -> None:
    if consent_status == "granted" and not evidence_key:
        raise HTTPException(
            status_code=422,
            detail="granted consent requires consent_evidence_key",
        )


@router.get("", response_model=list[VoiceProfileResponse])
def list_voice_profiles(
    project_id: UUID | None = None,
    speaker_id: str | None = None,
    consent_status: str | None = None,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_admin(identity, db)
    stmt = select(VoiceProfile).order_by(VoiceProfile.created_at.desc())
    if project_id:
        stmt = stmt.where(VoiceProfile.project_id == project_id)
    if speaker_id:
        stmt = stmt.where(VoiceProfile.speaker_id == speaker_id)
    if consent_status:
        stmt = stmt.where(VoiceProfile.consent_status == consent_status)
    rows = db.execute(stmt).scalars().all()
    return [_to_response(row) for row in rows]


@router.post("", response_model=VoiceProfileResponse, status_code=201)
def create_voice_profile(
    payload: VoiceProfileCreate,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_admin(identity, db)
    _ensure_evidence(payload.consent_status, payload.consent_evidence_key)
    now = datetime.now(timezone.utc)
    profile = VoiceProfile(
        project_id=payload.project_id,
        speaker_id=payload.speaker_id,
        reference_audio_key=payload.reference_audio_key,
        consent_status=payload.consent_status,
        consent_evidence_key=payload.consent_evidence_key,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
    db.flush()
    db.add(AuditLog(
        entity_type="voice_profile",
        entity_id=str(profile.id),
        action="created",
        actor=identity.email,
        payload={"consent_status": payload.consent_status},
    ))
    db.commit()
    return _to_response(profile)


@router.put("/{profile_id}", response_model=VoiceProfileResponse)
def update_voice_profile(
    profile_id: UUID,
    payload: VoiceProfileUpdate,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    _require_admin(identity, db)
    profile = db.get(VoiceProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="voice profile not found")
    _ensure_transition(profile.consent_status, payload.consent_status)
    evidence = payload.consent_evidence_key or profile.consent_evidence_key
    _ensure_evidence(payload.consent_status, evidence)
    profile.consent_status = payload.consent_status
    profile.consent_evidence_key = evidence
    if payload.reference_audio_key:
        profile.reference_audio_key = payload.reference_audio_key
    profile.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        entity_type="voice_profile",
        entity_id=str(profile.id),
        action=f"consent_{payload.consent_status}",
        actor=identity.email,
        payload={"consent_evidence_key": evidence},
    ))
    db.commit()
    return _to_response(profile)


def _to_response(profile: VoiceProfile) -> VoiceProfileResponse:
    return VoiceProfileResponse(
        id=profile.id,
        project_id=profile.project_id,
        speaker_id=profile.speaker_id,
        consent_status=profile.consent_status,
        reference_audio_key=profile.reference_audio_key,
        consent_evidence_key=profile.consent_evidence_key,
        embedding_storage_key=profile.embedding_storage_key,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )