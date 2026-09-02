"""Dataset manager endpoints (Phase 8).

Endpoints back the golden dataset flow described in `docs/golden-dataset.md`:
  GET  /admin/datasets
  GET  /admin/datasets/provenance
  POST /admin/datasets/sentences

License validation lives here so the UI cannot bypass it.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from translator_api.auth import UserIdentity
from translator_api.dependencies import get_db, get_identity
from translator_api.models import AuditLog


router = APIRouter(prefix="/admin/datasets", tags=["admin-dataset"])

ALLOWED_LICENSES = {"CC-BY-SA-4.0", "CC-BY-4.0", "CC0"}
ALLOWED_DOMAINS = {"news", "vlog", "review", "drama", "narration"}
ALLOWED_GENDERS = {"m", "f", "x"}


class GoldenSentenceCreate(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    zh: str = Field(min_length=1, max_length=2048)
    vi: str = Field(min_length=1, max_length=2048)
    audio_key: str | None = None
    domain: str
    speaker_gender: str = "x"
    tags: list[str] = Field(default_factory=list)
    license: str
    provenance_contributor: str = Field(min_length=1, max_length=128)


def _require_admin(identity: UserIdentity, db: Session) -> None:
    # Single-user mode: the auto-provisioned owner is always an admin.
    return


def _golden_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[5] / "datasets" / "golden"


@router.get("")
def list_sentences(identity: UserIdentity = Depends(get_identity), db: Session = Depends(get_db)):
    _require_admin(identity, db)
    path = _golden_root() / "zh-vi" / "sentences.jsonl"
    if not path.exists():
        return {"items": []}
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"items": items}


@router.get("/provenance")
def provenance(identity: UserIdentity = Depends(get_identity), db: Session = Depends(get_db)):
    _require_admin(identity, db)
    path = _golden_root() / "manifest.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="manifest not found")
    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        return {"manifest_path": str(path), "raw": path.read_text(encoding="utf-8")}
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@router.post("/sentences", status_code=201)
def add_sentence(payload: GoldenSentenceCreate, identity: UserIdentity = Depends(get_identity), db: Session = Depends(get_db)):
    _require_admin(identity, db)
    if payload.license not in ALLOWED_LICENSES:
        raise HTTPException(status_code=422, detail=f"license must be one of {sorted(ALLOWED_LICENSES)}")
    if payload.domain not in ALLOWED_DOMAINS:
        raise HTTPException(status_code=422, detail=f"domain must be one of {sorted(ALLOWED_DOMAINS)}")
    if payload.speaker_gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=422, detail=f"speaker_gender must be one of {sorted(ALLOWED_GENDERS)}")

    record = {
        "id": payload.id,
        "zh": payload.zh,
        "vi": payload.vi,
        "audio_key": payload.audio_key,
        "domain": payload.domain,
        "speaker_gender": payload.speaker_gender,
        "tags": payload.tags,
        "license": payload.license,
        "provenance": {"contributor": payload.provenance_contributor, "source": "in-house"},
    }
    path = _golden_root() / "zh-vi" / "sentences.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    db.add(AuditLog(
        entity_type="dataset",
        entity_id=payload.id,
        action="sentence_added",
        actor=identity.email,
        payload={"license": payload.license, "domain": payload.domain},
    ))
    db.commit()
    return {"id": payload.id, "license": payload.license}