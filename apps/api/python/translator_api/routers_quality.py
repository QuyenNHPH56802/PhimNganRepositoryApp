"""Quality scoring endpoints for translation segments.

Implements GET /projects/{project_id}/quality which runs the rule-based QA
provider against all translation segments and returns per-segment scores.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as SA_Session, joinedload

from translator_api.auth_dependency import get_current_user_optional
from translator_api.db import get_db
from translator_api.models import Glossary, GlossaryTerm, Project, TranslationSegment
from translator_api.providers.base import ProviderContext
from translator_api.providers.qa.rule_based import RuleBasedQaProvider, QaInput
from translator_shared.provider_responses_extra import QaIssue, QaStats, QaReport

router = APIRouter(prefix="/projects/{project_id}/quality", tags=["quality"])


# ─── Schemas ─────────────────────────────────────────────────────────────

class SegmentIssue(BaseModel):
    kind: str
    message: str
    severity: str  # "error" | "warn"


class SegmentScore(BaseModel):
    segment_id: UUID
    idx: int
    source_text: str
    display_text: str
    status: str
    issues: list[SegmentIssue]
    passed: bool
    qa_status: str  # "pass" | "warn" | "fail"


class QualityReportSchema(BaseModel):
    project_id: UUID
    total_segments: int
    passed_segments: int
    failed_segments: int
    warning_segments: int
    overall_passed: bool
    stats: QaStats | None
    segments: list[SegmentScore]


# ─── Helpers ─────────────────────────────────────────────────────────────

class _FakeSeg:
    """Lightweight stand-in for TranslationSegment so the QA provider can read .idx / .display_text."""
    __slots__ = ("idx", "display_text")
    def __init__(self, idx: int, display_text: str) -> None:
        self.idx = idx
        self.display_text = display_text


class _FakeTerm:
    """Stand-in for GlossaryTerm."""
    __slots__ = ("chinese", "vietnamese", "priority")
    def __init__(self, chinese: str, vietnamese: str, priority: int) -> None:
        self.chinese = chinese
        self.vietnamese = vietnamese
        self.priority = priority


def _run_qa(
    project_id: UUID,
    segments: list[TranslationSegment],
    db: SA_Session,
) -> QualityReportSchema:
    # Load active glossary.
    glossary = (
        db.execute(
            select(Glossary).where(
                Glossary.project_id == project_id,
                Glossary.is_active.is_(True),
            )
        )
        .scalars()
        .first()
    )
    glossary_terms = list(glossary.terms) if glossary else []

    # Source text map (transcript_segment.text keyed by idx).
    source_map: dict[int, str] = {
        seg.idx: getattr(seg.transcript_segment, "text", "") or ""
        for seg in segments
    }

    # Build QA payload.
    payload = QaInput(
        source_segments=[{"idx": s.idx, "text": source_map.get(s.idx, "")} for s in segments],
        translations=[_FakeSeg(s.idx, s.display_text or "") for s in segments],  # noqa: arg-type
        glossary=[_FakeTerm(t.chinese, t.vietnamese, t.priority) for t in glossary_terms],
    )

    ctx = ProviderContext(project_id=project_id)
    report: QaReport = RuleBasedQaProvider().run(payload, ctx=ctx)

    # Index issues by segment idx.
    issues_by_idx: dict[int, list[QaIssue]] = {}
    for issue in report.issues:
        issues_by_idx.setdefault(issue.segment_idx, []).append(issue)

    scored: list[SegmentScore] = []
    for seg in segments:
        seg_issues = issues_by_idx.get(seg.idx, [])
        has_error = any(i.severity == "error" for i in seg_issues)
        has_warn = any(i.severity == "warn" for i in seg_issues)
        passed = not has_error
        scored.append(
            SegmentScore(
                segment_id=seg.id,
                idx=seg.idx,
                source_text=source_map.get(seg.idx, ""),
                display_text=seg.display_text or "",
                status=seg.status,
                issues=[
                    SegmentIssue(kind=i.kind, message=i.message, severity=i.severity)
                    for i in seg_issues
                ],
                passed=passed,
                qa_status="fail" if has_error else ("warn" if has_warn else "pass"),
            )
        )

    return QualityReportSchema(
        project_id=project_id,
        total_segments=len(segments),
        passed_segments=sum(1 for s in scored if s.qa_status == "pass"),
        failed_segments=sum(1 for s in scored if s.qa_status == "fail"),
        warning_segments=sum(1 for s in scored if s.qa_status == "warn"),
        overall_passed=report.passed,
        stats=report.stats,
        segments=scored,
    )


# ─── Endpoints ───────────────────────────────────────────────────────────

@router.get("", response_model=QualityReportSchema)
def get_quality_report(
    project_id: UUID,
    db: SA_Session = Depends(get_db),
    _user: object | None = Depends(get_current_user_optional),
) -> QualityReportSchema:
    """Run QA on all translation segments and return a per-segment scorecard."""
    proj = db.get(Project, project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")

    segments = (
        db.execute(
            select(TranslationSegment)
            .options(joinedload(TranslationSegment.transcript_segment))
            .where(TranslationSegment.project_id == project_id)
            .order_by(TranslationSegment.idx)
        )
        .scalars()
        .unique()
        .all()
    )

    if not segments:
        raise HTTPException(status_code=404, detail="No translation segments found")

    return _run_qa(project_id, list(segments), db)
