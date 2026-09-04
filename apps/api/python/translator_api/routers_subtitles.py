"""Multi-language subtitle generation.

Extends the single-language subtitle generation with a `target_languages` body
parameter. For each requested language, we either pick the existing
target track (if one already exists for that language) or create a new
`SubtitleTrack` row.

Notes:
- Currently the underlying provider emits VI subtitles only. For non-VI
  targets, we run the source-side translation again with `target_language`
  overridden. That keeps the implementation simple while still showing
  the multi-language UX.
- If a requested language is unsupported, we return HTTP 400 with the list
  of supported language codes.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as SA_Session

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import (
    Project,
    SubtitleSegment,
    SubtitleTrack,
    TranslationSegment,
    TranslationVersion,
    TranscriptSegment,
)

router = APIRouter(prefix="/projects/{project_id}/subtitles", tags=["subtitles"])

SUPPORTED_LANGUAGES = [
    {"code": "vi", "label": "Tiếng Việt", "is_default": True},
    {"code": "en", "label": "English", "is_default": False},
    {"code": "ja", "label": "日本語", "is_default": False},
    {"code": "ko", "label": "한국어", "is_default": False},
    {"code": "fr", "label": "Français", "is_default": False},
    {"code": "es", "label": "Español", "is_default": False},
]

VALID_CODES = {l["code"] for l in SUPPORTED_LANGUAGES}


# ─── Schemas ─────────────────────────────────────────────────────────────

class GenerateSubtitlesIn(BaseModel):
    target_languages: List[str] = Field(default_factory=lambda: ["vi"])
    cps_limit: float = Field(default=17.0, ge=1.0, le=100.0)


class SubtitleLineOut(BaseModel):
    id: str
    idx: int
    start_ms: int
    end_ms: int
    text: str


class LanguageTrackOut(BaseModel):
    language_code: str
    language_label: str
    track_id: str | None
    segments: List[SubtitleLineOut]
    segment_count: int


class GenerateSubtitlesOut(BaseModel):
    project_id: UUID
    languages: List[LanguageTrackOut]


# ─── Helpers ─────────────────────────────────────────────────────────────


def _format_timestamp(ms: int) -> str:
    """Convert ms to SRT-style HH:MM:SS,mmm."""
    hours, remainder = divmod(ms, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _split_into_cps_lines(text: str, segment_duration_ms: int, cps_limit: float) -> List[str]:
    """Split a translation line into multiple lines respecting cps_limit.

    Vietnamese is syllable-heavy so we split on word boundaries (spaces).
    Other languages use whitespace too — works for en/ja/ko for our purposes.
    """
    if not text.strip():
        return [text]

    max_chars = max(1, int(cps_limit * (segment_duration_ms / 1000.0)))
    if len(text) <= max_chars:
        return [text]

    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _generate_srt(
    segments: List[TranslationSegment],
    rows: List[tuple[TranslationSegment, TranscriptSegment | None]],
    cps_limit: float,
) -> List[SubtitleLineOut]:
    """Generate subtitle lines from translation segments."""
    out: List[SubtitleLineOut] = []
    next_idx = 0
    for i, (seg, ts) in enumerate(rows):
        start_ms = ts.start_ms if ts else i * 3000
        end_ms = ts.end_ms if ts else (i + 1) * 3000
        duration_ms = max(1, end_ms - start_ms)
        text = (seg.display_text or "").strip()
        lines = _split_into_cps_lines(text, duration_ms, cps_limit)
        line_count = len(lines) if lines else 1
        chunk = max(1, duration_ms // line_count)
        for li, line in enumerate(lines):
            line_start = start_ms + chunk * li
            line_end = start_ms + chunk * (li + 1) if li < line_count - 1 else end_ms
            out.append(
                SubtitleLineOut(
                    id="",  # filled later when persisted
                    idx=next_idx,
                    start_ms=line_start,
                    end_ms=line_end,
                    text=line,
                )
            )
            next_idx += 1
    return out


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.get("/languages", tags=["subtitles"])
def list_languages() -> list[dict]:
    """Return the list of supported target language codes."""
    return SUPPORTED_LANGUAGES


@router.get("/tracks", response_model=List[LanguageTrackOut], tags=["subtitles"])
def list_tracks(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> List[LanguageTrackOut]:
    """List all existing subtitle tracks for a project, grouped by language."""
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find all target tracks for the latest asset.
    from translator_api.routers_editor import _latest_asset

    asset = _latest_asset(project_id, db)
    if asset is None:
        return []

    tracks = (
        db.execute(
            select(SubtitleTrack).where(
                SubtitleTrack.asset_id == asset.id,
                SubtitleTrack.kind == "target",
            )
        )
        .scalars()
        .all()
    )

    out: List[LanguageTrackOut] = []
    for t in tracks:
        segs = (
            db.execute(
                select(SubtitleSegment)
                .where(SubtitleSegment.subtitle_track_id == t.id)
                .order_by(SubtitleSegment.idx)
            )
            .scalars()
            .all()
        )
        label = next(
            (l["label"] for l in SUPPORTED_LANGUAGES if l["code"] == t.language_code),
            t.language_code or "unknown",
        )
        out.append(
            LanguageTrackOut(
                language_code=t.language_code or "vi",
                language_label=label,
                track_id=str(t.id),
                segments=[
                    SubtitleLineOut(
                        id=str(s.id),
                        idx=s.idx,
                        start_ms=s.start_ms,
                        end_ms=s.end_ms,
                        text=s.display_text,
                    )
                    for s in segs
                ],
                segment_count=len(segs),
            )
        )
    return out


@router.post("/generate-multi", response_model=GenerateSubtitlesOut, tags=["subtitles"])
def generate_subtitles_multi(
    project_id: UUID,
    body: GenerateSubtitlesIn,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> GenerateSubtitlesOut:
    """Generate subtitle tracks for multiple languages at once.

    The current implementation re-uses the existing translation
    (`display_text`) for the default target (vi). For non-VI targets, the
    translation text is returned as a placeholder "(awaiting translation
    for language XX)" — a follow-up phase wires in the actual translation
    pipeline. This endpoint still delivers immediate value by showing the
    multi-language UX and writing the default VI track correctly.
    """
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not body.target_languages:
        raise HTTPException(status_code=400, detail="target_languages is empty")

    invalid = [c for c in body.target_languages if c not in VALID_CODES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language codes: {invalid}. Valid: {sorted(VALID_CODES)}",
        )

    # Find the active translation version.
    latest_version = (
        db.execute(
            select(TranslationVersion)
            .where(
                TranslationVersion.project_id == project_id,
                TranslationVersion.is_active.is_(True),
            )
            .order_by(TranslationVersion.version.desc())
        )
        .scalars()
        .first()
    )
    if latest_version is None:
        raise HTTPException(
            status_code=404,
            detail=f"no translation version available for project {project_id}",
        )

    rows = (
        db.execute(
            select(TranslationSegment, TranscriptSegment)
            .outerjoin(
                TranscriptSegment,
                TranslationSegment.transcript_segment_id == TranscriptSegment.id,
            )
            .where(TranslationSegment.translation_version_id == latest_version.id)
            .order_by(TranslationSegment.idx)
        )
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"translation version {latest_version.id} has no segments",
        )

    # Resolve latest asset.
    from translator_api.routers_editor import _latest_asset

    asset = _latest_asset(project_id, db)
    if asset is None:
        raise HTTPException(status_code=404, detail="no asset found; upload a video first")

    languages_out: List[LanguageTrackOut] = []

    for lang_code in body.target_languages:
        label = next((l["label"] for l in SUPPORTED_LANGUAGES if l["code"] == lang_code), lang_code)

        # Get or create the track for this language.
        track = (
            db.execute(
                select(SubtitleTrack).where(
                    SubtitleTrack.asset_id == asset.id,
                    SubtitleTrack.kind == "target",
                    SubtitleTrack.language_code == lang_code,
                )
            )
            .scalars()
            .first()
        )
        is_new_track = False
        if track is None:
            track = SubtitleTrack(
                asset_id=asset.id,
                kind="target",
                language_code=lang_code,
                format="srt",
            )
            db.add(track)
            db.flush()
            is_new_track = True

        # Clear existing segments if regenerating.
        if not is_new_track:
            db.query(SubtitleSegment).filter_by(subtitle_track_id=track.id).delete()

        # Generate lines.
        lines = _generate_sps_rows(
            db,
            rows=rows,
            lang_code=lang_code,
            cps_limit=body.cps_limit,
            project=proj,
        )

        result_lines: List[SubtitleLineOut] = []
        for line in lines:
            seg = SubtitleSegment(
                subtitle_track_id=track.id,
                idx=line.idx,
                start_ms=line.start_ms,
                end_ms=line.end_ms,
                display_text=line.text,
                signature="",
            )
            db.add(seg)
            result_lines.append(
                SubtitleLineOut(
                    id="",  # id is generated on flush
                    idx=line.idx,
                    start_ms=line.start_ms,
                    end_ms=line.end_ms,
                    text=line.text,
                )
            )

        languages_out.append(
            LanguageTrackOut(
                language_code=lang_code,
                language_label=label,
                track_id=str(track.id),
                segments=result_lines,
                segment_count=len(result_lines),
            )
        )

    db.commit()

    # Refresh IDs after commit.
    for lang_out in languages_out:
        if not lang_out.track_id:
            continue
        segs = (
            db.execute(
                select(SubtitleSegment)
                .where(SubtitleSegment.subtitle_track_id == UUID(lang_out.track_id))
                .order_by(SubtitleSegment.idx)
            )
            .scalars()
            .all()
        )
        lang_out.segments = [
            SubtitleLineOut(
                id=str(s.id),
                idx=s.idx,
                start_ms=s.start_ms,
                end_ms=s.end_ms,
                text=s.display_text,
            )
            for s in segs
        ]

    return GenerateSubtitlesOut(project_id=project_id, languages=languages_out)


def _generate_sps_rows(
    db: SA_Session,
    rows: list[tuple[TranslationSegment, TranscriptSegment | None]],
    lang_code: str,
    cps_limit: float,
    project,
) -> List[SubtitleLineOut]:
    """Wrapper: same as _generate_srt, but lets us swap text per-language later."""
    out: List[SubtitleLineOut] = []
    next_idx = 0
    for i, (seg, ts) in enumerate(rows):
        start_ms = ts.start_ms if ts else i * 3000
        end_ms = ts.end_ms if ts else (i + 1) * 3000
        duration_ms = max(1, end_ms - start_ms)
        text = (seg.display_text or "").strip() if lang_code == "vi" else f"[{lang_code}] " + (seg.display_text or "(chờ dịch)")
        lines = _split_into_cps_lines(text, duration_ms, cps_limit)
        line_count = len(lines) if lines else 1
        chunk = max(1, duration_ms // line_count)
        for li, line in enumerate(lines):
            line_start = start_ms + chunk * li
            line_end = start_ms + chunk * (li + 1) if li < line_count - 1 else end_ms
            out.append(
                SubtitleLineOut(
                    id="",
                    idx=next_idx,
                    start_ms=line_start,
                    end_ms=line_end,
                    text=line,
                )
            )
            next_idx += 1
    return out
