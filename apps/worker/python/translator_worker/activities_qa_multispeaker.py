"""Phase 7 multi-speaker QA activity."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from temporalio import activity

from translator_api.models import Workflow
from translator_api.repositories.workflow_repository import WorkflowStepRepository
from translator_worker.deps import make_worker_session_factory


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _latest_workflow(session, project_id: UUID):
    stmt = select(Workflow).where(Workflow.project_id == project_id).order_by(Workflow.started_at.desc()).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def _record(session, project_id: str, name: str, status: str, message: str | None = None) -> None:
    workflow = _latest_workflow(session, UUID(project_id))
    if workflow is None:
        return
    WorkflowStepRepository(session).upsert(
        type("Step", (), {
            "workflow_id": workflow.id,
            "name": name,
            "status": status,
            "progress_pct": 100 if status == "ready" else 0,
            "progress_message": message,
            "artifact_signature": None,
            "started_at": _now(),
            "ended_at": _now() if status in {"ready", "failed"} else None,
        })()
    )
    session.commit()


def _speaker_segments(per_speaker_transcripts: dict[str, list[str]]) -> dict[str, str]:
    return {spk: " ".join(lines) for spk, lines in per_speaker_transcripts.items()}


def _wer(reference: str, hypothesis: str) -> float | None:
    try:
        from jiwer import wer  # type: ignore[import-not-found]
    except Exception:
        return None
    if not reference.strip():
        return 0.0 if not hypothesis.strip() else 1.0
    return float(wer(reference, hypothesis))


@activity.defn(name="qa_per_speaker")
async def qa_per_speaker(project_id: str, per_speaker_transcripts: dict[str, list[str]], per_speaker_reference: dict[str, list[str]]) -> dict:
    factory = make_worker_session_factory()
    session = factory()
    try:
        _record(session, project_id, "qa_per_speaker", status="processing")

        reference_set = set(per_speaker_reference.keys())
        transcript_set = set(per_speaker_transcripts.keys())
        missing_speakers = sorted(reference_set - transcript_set)
        extra_speakers = sorted(transcript_set - reference_set)

        speakers = reference_set | transcript_set
        per_speaker_wer: dict[str, float | None] = {}
        for spk in sorted(speakers):
            ref_text = " ".join(per_speaker_reference.get(spk, []))
            hyp_text = " ".join(per_speaker_transcripts.get(spk, []))
            per_speaker_wer[spk] = _wer(ref_text, hyp_text)

        values = [v for v in per_speaker_wer.values() if isinstance(v, (int, float))]
        mean_wer = round(sum(values) / len(values), 4) if values else None
        turn_overlap_count = _detect_overlaps(per_speaker_transcripts)
        long_pause_ms = 1500

        result = {
            "missing_speakers": missing_speakers,
            "extra_speakers": extra_speakers,
            "per_speaker_wer": per_speaker_wer,
            "per_speaker_wer_mean": mean_wer,
            "turn_overlap_count": turn_overlap_count,
            "long_pause_threshold_ms": long_pause_ms,
        }
        _record(session, project_id, "qa_per_speaker", status="ready", message=f"missing={len(missing_speakers)} mean_wer={mean_wer}")
        return result
    finally:
        session.close()


def _detect_overlaps(per_speaker_transcripts: dict[str, list[str]]) -> int:
    counts: dict[str, int] = defaultdict(int)
    for lines in per_speaker_transcripts.values():
        for line in lines:
            m = re.match(r"\[(\d+):(\d+)\.(\d+)\]", line)
            if m:
                minutes, seconds, ms = int(m.group(1)), int(m.group(2)), int(m.group(3))
                key = f"{minutes * 60 + seconds:04d}.{ms}"
                counts[key] += 1
    return sum(1 for count in counts.values() if count > 1)