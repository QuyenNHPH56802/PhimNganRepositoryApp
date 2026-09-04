"""Project templates.

A template captures the configuration choices a user makes when creating a
project (quality mode, language profile, TTS provider id, translate provider
id, default glossary) so that creating a new project is one click.

Templates are user-scoped (owned by a user_id) — but for the MVP we just
keep them in-memory via a simple in-process store. A future migration can
add a `project_templates` table.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from translator_api.auth_dependency import get_current_user_optional

router = APIRouter(prefix="/templates", tags=["templates"])


# ─── Schemas ─────────────────────────────────────────────────────────────


class ProjectTemplateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=512)
    quality_mode: str = "balanced"
    language_profile: str = "zh-vi"
    source_language: str = "zh"
    target_language: str = "vi"
    tts_provider_id: str | None = None
    translate_provider_id: str | None = None
    glossary_id: UUID | None = None
    # Free-form config blob to allow provider-specific keys without touching the schema.
    config: dict[str, Any] = Field(default_factory=dict)


class ProjectTemplate(ProjectTemplateIn):
    id: UUID
    created_at: datetime
    use_count: int = 0


# ─── In-memory store (replace with DB in a follow-up) ────────────────────

_STORE: dict[UUID, ProjectTemplate] = {}


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.get("", response_model=list[ProjectTemplate])
def list_templates() -> list[ProjectTemplate]:
    return list(_STORE.values())


@router.post("", response_model=ProjectTemplate, status_code=status.HTTP_201_CREATED)
def create_template(body: ProjectTemplateIn) -> ProjectTemplate:
    template = ProjectTemplate(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        use_count=0,
        **body.model_dump(),
    )
    _STORE[template.id] = template
    return template


@router.get("/{template_id}", response_model=ProjectTemplate)
def get_template(template_id: UUID) -> ProjectTemplate:
    template = _STORE.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    return template


@router.put("/{template_id}", response_model=ProjectTemplate)
def update_template(template_id: UUID, body: ProjectTemplateIn) -> ProjectTemplate:
    template = _STORE.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    updated = ProjectTemplate(
        id=template.id,
        created_at=template.created_at,
        use_count=template.use_count,
        **body.model_dump(),
    )
    _STORE[template_id] = updated
    return updated


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: UUID) -> None:
    if template_id not in _STORE:
        raise HTTPException(status_code=404, detail="template not found")
    del _STORE[template_id]


@router.post("/{template_id}/duplicate", response_model=ProjectTemplate, status_code=201)
def duplicate_template(template_id: UUID) -> ProjectTemplate:
    template = _STORE.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    copy_template = copy.deepcopy(template)
    copy_template.id = uuid4()
    copy_template.created_at = datetime.now(timezone.utc)
    copy_template.use_count = 0
    copy_template.name = f"{template.name} (copy)"
    _STORE[copy_template.id] = copy_template
    return copy_template


@router.post("/{template_id}/apply", response_model=dict)
def apply_template(template_id: UUID) -> dict:
    """Mark a template as used (increments counter). Returns the template payload
    so the caller can pipe it straight into a project-creation request.
    """
    template = _STORE.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    template.use_count += 1
    return {
        "template_id": str(template.id),
        "use_count": template.use_count,
        "payload": {
            "quality_mode": template.quality_mode,
            "language_profile": template.language_profile,
            "source_language": template.source_language,
            "target_language": template.target_language,
            "tts_provider_id": template.tts_provider_id,
            "translate_provider_id": template.translate_provider_id,
            "glossary_id": str(template.glossary_id) if template.glossary_id else None,
            "config": template.config,
        },
    }
