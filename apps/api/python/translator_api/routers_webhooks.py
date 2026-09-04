"""Webhook CRUD + dispatch endpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import List
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import Project, User, Webhook, WebhookDelivery

router = APIRouter(prefix="/projects/{project_id}/webhooks", tags=["webhooks"])

SUPPORTED_EVENTS = [
    "workflow.completed",
    "workflow.failed",
    "workflow.progress",
    "render.ready",
    "translation.ready",
]

AVAILABLE_EVENTS = [
    {"id": e, "label": e} for e in SUPPORTED_EVENTS
]

# ─── Schemas ─────────────────────────────────────────────────────────────

class WebhookIn(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    description: str | None = Field(None, max_length=255)
    events: List[str] = Field(default_factory=list)
    secret: str | None = Field(None, min_length=16, max_length=255)


class WebhookOut(BaseModel):
    id: UUID
    project_id: UUID
    url: str
    description: str | None
    events: List[str]
    is_active: bool
    created_at: datetime
    secret_preview: str  # first 4 + last 4 chars


class WebhookDeliveryOut(BaseModel):
    id: UUID
    webhook_id: UUID
    event: str
    status_code: int | None
    success: bool
    attempt: int
    last_error: str | None
    created_at: datetime


class WebhookListOut(BaseModel):
    webhooks: List[WebhookOut]
    available_events: List[dict]


# ─── Helpers ─────────────────────────────────────────────────────────────

def _sign_payload(payload: str, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def _make_secret() -> str:
    return secrets.token_urlsafe(32)


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


# ─── Endpoints ───────────────────────────────────────────────────────────

@router.get("", response_model=WebhookListOut)
def list_webhooks(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> WebhookListOut:
    """List all webhooks for a project."""
    _ensure_project(db, project_id)
    hooks = (
        db.execute(
            select(Webhook)
            .where(Webhook.project_id == project_id)
            .order_by(Webhook.created_at.desc())
        )
        .scalars()
        .all()
    )
    out = [
        WebhookOut(
            id=h.id,
            project_id=h.project_id,
            url=h.url,
            description=h.description,
            events=h.events,
            is_active=h.is_active,
            created_at=h.created_at,
            secret_preview=_mask_secret(h.secret),
        )
        for h in hooks
    ]
    return WebhookListOut(webhooks=out, available_events=AVAILABLE_EVENTS)


@router.post("", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
def create_webhook(
    project_id: UUID,
    body: WebhookIn,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> WebhookOut:
    """Register a new webhook endpoint."""
    _ensure_project(db, project_id)
    for ev in body.events:
        if ev not in SUPPORTED_EVENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported event: {ev}. Valid: {SUPPORTED_EVENTS}",
            )
    secret = body.secret or _make_secret()
    hook = Webhook(
        project_id=project_id,
        url=body.url,
        description=body.description,
        events=list(body.events),
        secret=secret,
        created_at=datetime.now(timezone.utc),
    )
    db.add(hook)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Webhook for URL {body.url} already exists on this project",
        )
    db.refresh(hook)
    return WebhookOut(
        id=hook.id,
        project_id=hook.project_id,
        url=hook.url,
        description=hook.description,
        events=hook.events,
        is_active=hook.is_active,
        created_at=hook.created_at,
        secret_preview=_mask_secret(hook.secret),
    )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    project_id: UUID,
    webhook_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> None:
    hook = db.get(Webhook, webhook_id)
    if hook is None or hook.project_id != project_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(hook)
    db.commit()


@router.post("/{webhook_id}/toggle", response_model=WebhookOut)
def toggle_webhook(
    project_id: UUID,
    webhook_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> WebhookOut:
    hook = db.get(Webhook, webhook_id)
    if hook is None or hook.project_id != project_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    hook.is_active = not hook.is_active
    db.commit()
    return WebhookOut(
        id=hook.id,
        project_id=hook.project_id,
        url=hook.url,
        description=hook.description,
        events=hook.events,
        is_active=hook.is_active,
        created_at=hook.created_at,
        secret_preview=_mask_secret(hook.secret),
    )


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryOut])
def list_deliveries(
    project_id: UUID,
    webhook_id: UUID,
    limit: int = 20,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> List[WebhookDeliveryOut]:
    hook = db.get(Webhook, webhook_id)
    if hook is None or hook.project_id != project_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    rows = (
        db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        WebhookDeliveryOut(
            id=r.id,
            webhook_id=r.webhook_id,
            event=r.event,
            status_code=r.status_code,
            success=r.success,
            attempt=r.attempt,
            last_error=r.last_error,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryOut, status_code=201)
def send_test_webhook(
    project_id: UUID,
    webhook_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> WebhookDeliveryOut:
    """Send a test payload to the webhook URL and record the result."""
    hook = db.get(Webhook, webhook_id)
    if hook is None or hook.project_id != project_id:
        raise HTTPException(status_code=404, detail="Webhook not found")

    payload = {
        "event": "test",
        "project_id": str(project_id),
        "webhook_id": str(hook.id),
        "message": "Test webhook from China-VNE platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    delivery = _deliver_webhook(hook, "test", payload, db)
    return WebhookDeliveryOut(
        id=delivery.id,
        webhook_id=delivery.webhook_id,
        event=delivery.event,
        status_code=delivery.status_code,
        success=delivery.success,
        attempt=delivery.attempt,
        last_error=delivery.last_error,
        created_at=delivery.created_at,
    )


# ─── Dispatch helper ──────────────────────────────────────────────────────

async def dispatch_event(
    project_id: UUID,
    event: str,
    data: dict,
    db: SA_Session,
) -> None:
    """Fire an event to all active webhooks subscribed to it."""
    hooks = (
        db.execute(
            select(Webhook).where(
                Webhook.project_id == project_id,
                Webhook.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )
    matching = [h for h in hooks if event in h.events]
    for hook in matching:
        _deliver_webhook(hook, event, data, db)


def _deliver_webhook(
    hook: Webhook,
    event: str,
    data: dict,
    db: SA_Session,
) -> WebhookDelivery:
    payload_str = json.dumps(data, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ChinaVNE-Webhook/1.0",
        "X-Webhook-Event": event,
        "X-Webhook-ID": str(hook.id),
        "X-Webhook-Timestamp": str(int(datetime.now(timezone.utc).timestamp())),
    }
    headers["X-Webhook-Signature"] = _sign_payload(payload_str, hook.secret)

    delivery = WebhookDelivery(
        webhook_id=hook.id,
        event=event,
        payload=data,
        attempt=1,
        success=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(delivery)

    try:
        response = httpx.post(hook.url, content=payload_str, headers=headers, timeout=10.0)
        delivery.status_code = response.status_code
        delivery.response_body = response.text[:2000]
        delivery.success = 200 <= response.status_code < 300
        if not delivery.success:
            delivery.last_error = f"HTTP {response.status_code}"
    except httpx.TimeoutException:
        delivery.status_code = 0
        delivery.success = False
        delivery.last_error = "Timeout after 10s"
    except httpx.RequestError as exc:
        delivery.status_code = 0
        delivery.success = False
        delivery.last_error = str(exc)[:500]
    finally:
        db.commit()

    return delivery


def _mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    return secret[:4] + "****" + secret[-4:]
