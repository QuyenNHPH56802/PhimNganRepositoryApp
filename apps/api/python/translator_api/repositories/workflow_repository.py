"""Workflow + workflow step repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from translator_api.models import Workflow, WorkflowStep


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, workflow_id: UUID) -> Workflow | None:
        return self.db.get(Workflow, workflow_id)

    def get_by_temporal(self, temporal_workflow_id: str, temporal_run_id: str) -> Workflow | None:
        stmt = select(Workflow).where(
            Workflow.temporal_workflow_id == temporal_workflow_id,
            Workflow.temporal_run_id == temporal_run_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, workflow: Workflow) -> Workflow:
        workflow.started_at = datetime.now(timezone.utc)
        self.db.add(workflow)
        self.db.flush()
        return workflow

    def update_status(self, workflow: Workflow, status: str, *, last_error: dict | None = None) -> None:
        workflow.status = status
        workflow.last_error = last_error
        if status in {"ready", "archived", "failed"}:
            workflow.ended_at = datetime.now(timezone.utc)
        self.db.flush()


class WorkflowStepRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_workflow(self, workflow_id: UUID) -> list[WorkflowStep]:
        stmt = select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id).order_by(WorkflowStep.started_at.is_(None), WorkflowStep.started_at.asc())
        return list(self.db.execute(stmt).scalars())

    def upsert(self, step: WorkflowStep) -> WorkflowStep:
        existing = self.db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == step.workflow_id, WorkflowStep.name == step.name)
        ).scalar_one_or_none()
        if existing is None:
            self.db.add(step)
            self.db.flush()
            return step
        for field in ("status", "attempt", "progress_pct", "progress_message", "artifact_signature", "ended_at"):
            setattr(existing, field, getattr(step, field, getattr(existing, field)))
        if step.started_at is not None:
            existing.started_at = step.started_at
        self.db.flush()
        return existing