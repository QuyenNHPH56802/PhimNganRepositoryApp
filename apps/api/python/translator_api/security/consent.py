"""Consent workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from translator_api.models import AuditLog, VoiceProfile


class ConsentActionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConsentState:
    voice_profile_id: UUID
    status: str
    requested_at: datetime | None
    granted_at: datetime | None
    revoked_at: datetime | None


def request_consent(db: Session, voice_profile_id: UUID, *, actor: str, evidence_key: str) -> VoiceProfile:
    profile = db.get(VoiceProfile, voice_profile_id)
    if profile is None:
        raise ConsentActionError("voice profile not found")
    profile.consent_status = "requested"
    profile.consent_evidence_key = evidence_key
    db.add(AuditLog(entity_type="voice_profile", entity_id=str(voice_profile_id), action="consent_requested", payload={"actor": actor, "evidence_key": evidence_key}))
    db.flush()
    return profile


def grant_consent(db: Session, voice_profile_id: UUID, *, actor: str, evidence_key: str | None = None) -> VoiceProfile:
    profile = db.get(VoiceProfile, voice_profile_id)
    if profile is None:
        raise ConsentActionError("voice profile not found")
    if profile.consent_status not in {"requested", "revoked"}:
        raise ConsentActionError(f"cannot grant from {profile.consent_status}")
    profile.consent_status = "granted"
    if evidence_key:
        profile.consent_evidence_key = evidence_key
    db.add(AuditLog(entity_type="voice_profile", entity_id=str(voice_profile_id), action="consent_granted", payload={"actor": actor}))
    db.flush()
    return profile


def revoke_consent(db: Session, voice_profile_id: UUID, *, actor: str, reason: str) -> VoiceProfile:
    profile = db.get(VoiceProfile, voice_profile_id)
    if profile is None:
        raise ConsentActionError("voice profile not found")
    profile.consent_status = "revoked"
    db.add(AuditLog(entity_type="voice_profile", entity_id=str(voice_profile_id), action="consent_revoked", payload={"actor": actor, "reason": reason}))
    db.flush()
    return profile


def state_of(profile: VoiceProfile) -> ConsentState:
    return ConsentState(
        voice_profile_id=profile.id,
        status=profile.consent_status,
        requested_at=None,
        granted_at=None,
        revoked_at=None,
    )


def load_state(db: Session, voice_profile_id: UUID) -> ConsentState:
    profile = db.get(VoiceProfile, voice_profile_id)
    if profile is None:
        raise ConsentActionError("voice profile not found")
    return state_of(profile)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
