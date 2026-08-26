"""Phase 8 admin routes.

All endpoints require `role=OWNER` at the *project* level OR a global
`role=OWNER` flag on the user. The fastapi dependency `require_admin`
enforces this.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.auth import UserIdentity
from translator_api.dependencies import get_db, get_identity
from translator_api.models import AuditLog, User


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(identity: UserIdentity, db: Session) -> User:
    user = db.get(User, UUID(identity.user_id))
    if user is None or not user.is_admin:
        raise HTTPException(status_code=403, detail="admin role required")
    return user


@router.get("/audit-logs")
def list_audit_logs(
    entity: str | None = Query(None),
    action: str | None = Query(None),
    actor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    require_admin(identity, db)
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    if entity:
        stmt = stmt.where(AuditLog.entity_type == entity)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)
    logs = db.execute(stmt).scalars().all()
    return {
        "items": [
            {
                "id": str(log.id),
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "actor": log.actor,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "payload": log.payload,
            }
            for log in logs
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit-logs/{audit_id}")
def get_audit_log(audit_id: UUID, identity: UserIdentity = Depends(get_identity), db: Session = Depends(get_db)):
    require_admin(identity, db)
    log = db.get(AuditLog, audit_id)
    if log is None:
        raise HTTPException(status_code=404, detail="audit log not found")
    return {
        "id": str(log.id),
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "action": log.action,
        "actor": log.actor,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "payload": log.payload,
    }