"""Glossary CRUD endpoints.

Glossaries are per-project. Each project has 0..N glossary versions, but only
one is active (`is_active=True`). Adding terms to an inactive glossary
doesn't affect running translations until the user activates it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import Glossary, GlossaryTerm, Project, User

router = APIRouter(prefix="/projects/{project_id}/glossaries", tags=["glossary"])


# ─── Schemas ─────────────────────────────────────────────────────────────


class GlossaryTermIn(BaseModel):
    chinese: str = Field(..., min_length=1, max_length=512)
    vietnamese: str = Field(..., min_length=1, max_length=512)
    category: str | None = Field(None, max_length=64)
    rule: str | None = Field(None, max_length=64)
    priority: int = 0


class GlossaryTermOut(BaseModel):
    id: UUID
    chinese: str
    vietnamese: str
    category: str | None = None
    rule: str | None = None
    priority: int
    is_active: bool

    class Config:
        from_attributes = True


class GlossaryOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    version: int
    created_at: datetime
    is_active: bool
    terms: List[GlossaryTermOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class GlossaryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    terms: List[GlossaryTermIn] = Field(default_factory=list)
    activate: bool = True


class GlossaryActivateResponse(BaseModel):
    id: UUID
    is_active: bool


# ─── Helpers ─────────────────────────────────────────────────────────────


def _ensure_project(db: SA_Session, project_id: UUID) -> Project:
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


def _serialize(g: Glossary) -> GlossaryOut:
    return GlossaryOut(
        id=g.id,
        project_id=g.project_id,
        name=g.name,
        version=g.version,
        created_at=g.created_at,
        is_active=g.is_active,
        terms=[
            GlossaryTermOut(
                id=t.id,
                chinese=t.chinese,
                vietnamese=t.vietnamese,
                category=t.category,
                rule=t.rule,
                priority=t.priority,
                is_active=t.is_active,
            )
            for t in g.terms
        ],
    )


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.get("", response_model=List[GlossaryOut])
def list_glossaries(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> List[GlossaryOut]:
    """List all glossary versions for a project (newest first)."""
    _ensure_project(db, project_id)
    glossaries = (
        db.execute(
            select(Glossary)
            .where(Glossary.project_id == project_id)
            .order_by(Glossary.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [_serialize(g) for g in glossaries]


@router.get("/active", response_model=GlossaryOut | None)
def get_active_glossary(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> GlossaryOut | None:
    """Return the currently active glossary for the project, or None."""
    _ensure_project(db, project_id)
    g = (
        db.execute(
            select(Glossary).where(
                Glossary.project_id == project_id, Glossary.is_active.is_(True)
            )
        )
        .scalars()
        .first()
    )
    return _serialize(g) if g else None


@router.post("", response_model=GlossaryOut, status_code=status.HTTP_201_CREATED)
def create_glossary(
    project_id: UUID,
    body: GlossaryCreate,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> GlossaryOut:
    """Create a new glossary version. If activate=True, deactivate all others."""
    _ensure_project(db, project_id)
    if body.activate:
        # Mark every existing glossary as inactive atomically.
        db.execute(
            Glossary.__table__.update()
            .where(Glossary.project_id == project_id)
            .values(is_active=False)
        )

    # Compute next version number.
    max_version = (
        db.execute(
            select(Glossary.version)
            .where(Glossary.project_id == project_id)
            .order_by(Glossary.version.desc())
            .limit(1)
        ).scalar_one_or_none()
    ) or 0

    g = Glossary(
        project_id=project_id,
        name=body.name,
        version=max_version + 1,
        created_at=datetime.now(timezone.utc),
        is_active=body.activate,
        terms=[
            GlossaryTerm(
                chinese=t.chinese,
                vietnamese=t.vietnamese,
                category=t.category,
                rule=t.rule,
                priority=t.priority,
            )
            for t in body.terms
        ],
    )
    db.add(g)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate chinese term in glossary")
    db.refresh(g)
    return _serialize(g)


@router.post("/{glossary_id}/activate", response_model=GlossaryActivateResponse)
def activate_glossary(
    project_id: UUID,
    glossary_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> GlossaryActivateResponse:
    """Mark a glossary version as active. Deactivates others in the same project."""
    g = db.get(Glossary, glossary_id)
    if g is None or g.project_id != project_id:
        raise HTTPException(status_code=404, detail="Glossary not found")
    db.execute(
        Glossary.__table__.update()
        .where(Glossary.project_id == project_id)
        .values(is_active=False)
    )
    g.is_active = True
    db.commit()
    return GlossaryActivateResponse(id=g.id, is_active=True)


@router.delete("/{glossary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary(
    project_id: UUID,
    glossary_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> None:
    """Permanently delete a glossary version."""
    g = db.get(Glossary, glossary_id)
    if g is None or g.project_id != project_id:
        raise HTTPException(status_code=404, detail="Glossary not found")
    db.delete(g)
    db.commit()


@router.post("/{glossary_id}/terms", response_model=GlossaryOut, status_code=201)
def add_term(
    project_id: UUID,
    glossary_id: UUID,
    body: GlossaryTermIn,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> GlossaryOut:
    """Add a single term to an existing glossary."""
    g = db.get(Glossary, glossary_id)
    if g is None or g.project_id != project_id:
        raise HTTPException(status_code=404, detail="Glossary not found")
    term = GlossaryTerm(
        glossary_id=g.id,
        chinese=body.chinese,
        vietnamese=body.vietnamese,
        category=body.category,
        rule=body.rule,
        priority=body.priority,
    )
    db.add(term)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Term '{body.chinese}' already exists in this glossary",
        )
    db.refresh(g)
    return _serialize(g)


@router.delete(
    "/{glossary_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_term(
    project_id: UUID,
    glossary_id: UUID,
    term_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: User | None = Depends(get_current_user_optional),
) -> None:
    """Remove a single term from a glossary."""
    g = db.get(Glossary, glossary_id)
    if g is None or g.project_id != project_id:
        raise HTTPException(status_code=404, detail="Glossary not found")
    term = next((t for t in g.terms if t.id == term_id), None)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(term)
    db.commit()
