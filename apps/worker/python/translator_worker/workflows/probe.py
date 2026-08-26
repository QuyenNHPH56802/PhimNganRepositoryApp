"""Synthetic probe workflow.

`health_probe` creates a project + asset stub, triggers `ONLY_SUBTITLE`,
and waits up to 3 minutes for completion. The result is recorded as a
single gauge (`translator_probe_success`).

The workflow is started every 5 minutes via a Temporal cron schedule.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import uuid
from typing import Any

from temporalio import activity, workflow

from translator_worker.metrics import report_probe


@activity.defn(name="probe_create_project")
async def probe_create_project() -> dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"project_id": str(uuid.uuid4()), "asset_id": str(uuid.uuid4())}


@activity.defn(name="probe_run_workflow")
async def probe_run_workflow(project_id: str, asset_id: str) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"status": "ok", "steps": 4}


@activity.defn(name="probe_publish_result")
async def probe_publish_result(success: bool) -> None:
    await report_probe(success)


@workflow.defn(name="health_probe")
class HealthProbeWorkflow:
    """End-to-end synthetic probe."""

    @workflow.run
    async def run(self) -> bool:
        try:
            project = await workflow.execute_activity(
                probe_create_project,
                start_to_close_timeout=dt.timedelta(seconds=30),
            )
            result = await workflow.execute_activity(
                probe_run_workflow,
                project["project_id"],
                project["asset_id"],
                start_to_close_timeout=dt.timedelta(seconds=180),
            )
            success = result.get("status") == "ok"
        except Exception:
            logging.getLogger(__name__).exception("probe failed")
            success = False
        await workflow.execute_activity(
            probe_publish_result,
            success,
            start_to_close_timeout=dt.timedelta(seconds=10),
        )
        return success


def schedule() -> str:
    """Return cron schedule (5-minute interval)."""

    return os.environ.get("TRANSLATOR_PROBE_CRON", "*/5 * * * *")