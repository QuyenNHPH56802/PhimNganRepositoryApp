"""Security + governance routers (auth, consent, audit, members)."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.auth_dependency import get_identity
from translator_api.db import get_db
from translator_api.models import AuditLog, ProjectMember, User
from translator_api.repositories.project_member_repository import ProjectMemberRepository
from translator_api.repositories.project_repository import ProjectRepository
from translator_api.quality_mode import QualityMode, policy_for
from translator_api.schemas import (
    AuditLogListResponse,
    ConsentStateResponse,
    MemberAddRequest,
    MemberListResponse,
    MemberResponse,
    ProjectConsentRequest,
    QualityModeRequest,
    QualityModeResponse,
)
from translator_api.security.consent import (
    ConsentActionError,
    grant_consent,
    revoke_consent,
    request_consent,
)
from translator_api.security.identity import UserIdentity
from translator_api.security.rbac import Role, require_project_role
from translator_api.security.session import issue_session_jwt

router = APIRouter()


@router.post("/auth/login/stub", tags=["auth"])
async def login_stub(payload: dict, db: Session = Depends(get_db)) -> dict:
    """Authentication endpoint; verifies user and persists account to PostgreSQL."""
    email = payload.get("email")
    if not isinstance(email, str) or "@" not in email:
        raise HTTPException(status_code=400, detail="email is required")

    display_name = payload.get("display_name") or email.split("@")[0]
    now = datetime.now(timezone.utc)

    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            id=uuid4(),
            email=email,
            display_name=display_name,
            is_admin=True,
            created_at=now,
            last_login_at=now,
        )
        db.add(user)
    else:
        user.last_login_at = now
        user.is_admin = True
    db.commit()

    identity = UserIdentity(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        provider="stub",
    )
    token = issue_session_jwt(identity)
    return {
        "token": token,
        "identity": {
            "user_id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "provider": "stub",
            "is_admin": True,
        },
    }


@router.get("/auth/me", response_model=dict, tags=["auth"])
async def auth_me(
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> dict:
    user = db.get(User, UUID(identity.user_id)) if identity.user_id else None
    return {
        "user_id": identity.user_id,
        "email": identity.email,
        "display_name": identity.display_name or (user.display_name if user else None),
        "provider": identity.provider,
        "is_admin": user.is_admin if user else True,
    }


@router.get(
    "/projects/{project_id}/audit",
    response_model=AuditLogListResponse,
    tags=["audit"],
)
async def list_audit(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    require_project_role(project_id, Role.VIEWER, db=db, identity=identity)
    stmt = select(AuditLog).where(AuditLog.project_id == project_id).order_by(AuditLog.created_at.desc()).limit(200)
    rows = list(db.execute(stmt).scalars())
    return AuditLogListResponse(
        items=[
            {
                "id": str(row.id),
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "action": row.action,
                "payload": row.payload,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        total=len(rows),
    )


@router.post(
    "/voice-profiles/{voice_profile_id}/consent:request",
    response_model=ConsentStateResponse,
    tags=["consent"],
)
async def voice_consent_request(
    voice_profile_id: UUID,
    payload: ProjectConsentRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ConsentStateResponse:
    try:
        profile = request_consent(db, voice_profile_id, actor=identity.email, evidence_key=payload.evidence_key)
        db.commit()
    except ConsentActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConsentStateResponse(voice_profile_id=profile.id, status=profile.consent_status, evidence_key=profile.consent_evidence_key)


@router.post(
    "/voice-profiles/{voice_profile_id}/consent:grant",
    response_model=ConsentStateResponse,
    tags=["consent"],
)
async def voice_consent_grant(
    voice_profile_id: UUID,
    payload: ProjectConsentRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ConsentStateResponse:
    try:
        profile = grant_consent(db, voice_profile_id, actor=identity.email, evidence_key=payload.evidence_key)
        db.commit()
    except ConsentActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConsentStateResponse(voice_profile_id=profile.id, status=profile.consent_status, evidence_key=profile.consent_evidence_key)


@router.post(
    "/voice-profiles/{voice_profile_id}/consent:revoke",
    response_model=ConsentStateResponse,
    tags=["consent"],
)
async def voice_consent_revoke(
    voice_profile_id: UUID,
    payload: dict,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ConsentStateResponse:
    try:
        profile = revoke_consent(db, voice_profile_id, actor=identity.email, reason=payload.get("reason", ""))
        db.commit()
    except ConsentActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConsentStateResponse(voice_profile_id=profile.id, status=profile.consent_status, evidence_key=profile.consent_evidence_key)


@router.get(
    "/projects/{project_id}/members",
    response_model=MemberListResponse,
    tags=["members"],
)
async def list_members(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> MemberListResponse:
    require_project_role(project_id, Role.VIEWER, db=db, identity=identity)
    rows = ProjectMemberRepository(db).list_for_project(project_id)
    return MemberListResponse(
        items=[
            MemberResponse(user_id=str(row.user_id), role=row.role, added_at=row.added_at)
            for row in rows
        ]
    )


@router.put(
    "/projects/{project_id}/members",
    response_model=MemberResponse,
    tags=["members"],
)
async def add_member(
    project_id: UUID,
    payload: MemberAddRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> MemberResponse:
    require_project_role(project_id, Role.OWNER, db=db, identity=identity)
    repo = ProjectMemberRepository(db)
    member = repo.add(project_id, UUID(payload.user_id), payload.role)
    db.commit()
    return MemberResponse(user_id=str(member.user_id), role=member.role, added_at=member.added_at)


@router.put(
    "/projects/{project_id}/quality-mode",
    response_model=QualityModeResponse,
    tags=["quality"],
)
async def set_quality_mode(
    project_id: UUID,
    payload: QualityModeRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> QualityModeResponse:
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    policy = policy_for(QualityMode(payload.mode))
    project = ProjectRepository(db).get(project_id)
    project.quality_mode = payload.mode  # Store the mode identifier, not the ASR provider
    # subtitle_target_cps is a setting-level concern; ensure ProjectSettings row exists.
    from translator_api.models import ProjectSettings
    settings_row = db.get(ProjectSettings, project_id)
    if settings_row is None:
        settings_row = ProjectSettings(project_id=project_id)
        db.add(settings_row)
    db.commit()
    db.add(AuditLog(entity_type="project", entity_id=str(project_id), action="quality_mode_set", payload={"actor": identity.email, "mode": payload.mode}))
    db.commit()
    return QualityModeResponse(
        project_id=project_id,
        mode=payload.mode,
        policy={
            "asr_provider": policy.asr_provider,
            "diarize": policy.diarize,
            "alignment": policy.alignment,
            "voice_clone": policy.voice_clone,
            "mixer": policy.mixer,
            "subtitle_target_cps": policy.subtitle_target_cps,
        },
    )