"""Admin routes & governance overview."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from translator_api.auth import UserIdentity
from translator_api.dependencies import get_db, get_identity
from translator_api.models import AuditLog, Project, User, VoiceProfile, Workflow


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(identity: UserIdentity = Depends(get_identity), db: Session = Depends(get_db)) -> User:
    try:
        user_uuid = UUID(identity.user_id)
        user = db.get(User, user_uuid)
    except (ValueError, TypeError):
        user = None

    if user is None:
        # Dev / stub fallback: auto-upsert admin identity
        now = datetime.now(timezone.utc)
        user = User(
            id=UUID(identity.user_id) if identity.user_id and len(identity.user_id) == 36 else UUID("00000000-0000-0000-0000-000000000001"),
            email=identity.email or "admin@translator.local",
            display_name=identity.display_name or "Admin",
            is_admin=True,
            created_at=now,
            last_login_at=now,
        )
        db.add(user)
        db.commit()

    return user


@router.get("/overview")
def get_admin_overview(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """System-wide administration overview metrics."""
    total_projects = db.scalar(select(func.count(Project.id))) or 0
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_workflows = db.scalar(select(func.count(Workflow.id))) or 0
    total_voices = db.scalar(select(func.count(VoiceProfile.id))) or 0
    total_audits = db.scalar(select(func.count(AuditLog.id))) or 0

    return {
        "status": "healthy",
        "system_time": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "metrics": {
            "projects": total_projects,
            "users": total_users,
            "workflows": total_workflows,
            "voice_profiles": total_voices,
            "audit_logs": total_audits,
        },
        "admin_user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
        },
    }


@router.get("/audit-logs")
def list_audit_logs(
    entity: str | None = Query(None),
    action: str | None = Query(None),
    actor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    if entity:
        stmt = stmt.where(AuditLog.entity_type == entity)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor:
        stmt = stmt.where(AuditLog.entity_id == actor)
    logs = db.execute(stmt).scalars().all()
    return {
        "items": [
            {
                "id": str(log.id),
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "actor": str(log.user_id) if log.user_id else "system",
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "payload": log.payload,
            }
            for log in logs
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit-logs/{audit_id}")
def get_audit_log(
    audit_id: UUID,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    log = db.get(AuditLog, audit_id)
    if log is None:
        raise HTTPException(status_code=404, detail="audit log not found")
    return {
        "id": str(log.id),
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "action": log.action,
        "actor": str(log.user_id) if log.user_id else "system",
        "timestamp": log.created_at.isoformat() if log.created_at else None,
        "payload": log.payload,
    }
