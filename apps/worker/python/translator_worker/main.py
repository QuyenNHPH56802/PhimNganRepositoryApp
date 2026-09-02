"""Temporal worker entrypoint.

Phase 3 registers:
- ASR queue with asr_transcribe
- Diarize queue with diarize_segments
- TTS queue with tts_synthesize
- CPU queue with every other activity (translate, qa, subtitle, normalize,
  align, separate, mix, render, export, cleanup, validate, analyze,
  chunk_plan, detect_subtitle_stream)
- Project queue with all workflows + everything for legacy callers
"""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from translator_api.providers.registry import bootstrap
from translator_worker import activities, activities_phase3, activities_providers
from translator_worker.settings import get_settings
from translator_worker.workflows import (
    ASR_QUEUE,
    CPU_QUEUE,
    DIARIZE_QUEUE,
    TTS_QUEUE,
)

logger = logging.getLogger(__name__)

from translator_worker.constants import PROJECT_QUEUE


TRIVIAL_ACTIVITIES = [
    activities.validate_inputs,
    activities.detect_subtitle_stream,
    activities.analyze_media,
    activities.chunk_plan,
    # align_text / diarize_segments: their providers now degrade gracefully
    # (returning empty alignment / single-speaker fallback) instead of raising
    # when dependencies are missing, so the rest of the workflow can run
    # end-to-end.
    activities_providers.align_text,
]

PHASE3_ACTIVITIES = [
    activities_phase3.normalize_chinese,
    activities_phase3.translate_segments,
    activities_phase3.translation_qa,
    activities_phase3.subtitle_segment,
    activities_phase3.dubbing_align,
    activities_phase3.audio_mix,
    activities_phase3.render_build,
    activities_phase3.export_assemble,
    activities_phase3.cleanup_orphans,
]

CPU_ACTIVITIES = TRIVIAL_ACTIVITIES + PHASE3_ACTIVITIES
ASR_ACTIVITIES = [activities_providers.asr_transcribe]
DIARIZE_ACTIVITIES = [activities_providers.diarize_segments]
TTS_ACTIVITIES = [activities_phase3.tts_synthesize]
SEPARATION_ACTIVITIES = [activities_phase3.audio_separate]


async def main() -> None:
    import os
    os.environ.setdefault("TRANSLATOR_STORAGE_PROVIDER_ID", "local")
    # API key should be set via environment variable OPENAI_API_KEY
    bootstrap()
    settings = get_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)

    from translator_worker.workflows import (
        ChunkWorkflow,
        DubbingWorkflow,
        ProjectWorkflow,
        SubtitleWorkflow,
    )

    workflow_classes = [ProjectWorkflow, SubtitleWorkflow, DubbingWorkflow, ChunkWorkflow]

    workers = [
        Worker(
            client,
            task_queue=PROJECT_QUEUE,
            workflows=workflow_classes,
            activities=CPU_ACTIVITIES + ASR_ACTIVITIES + DIARIZE_ACTIVITIES + TTS_ACTIVITIES + SEPARATION_ACTIVITIES,
        ),
        Worker(client, task_queue=ASR_QUEUE, workflows=[], activities=ASR_ACTIVITIES),
        Worker(client, task_queue=DIARIZE_QUEUE, workflows=[], activities=DIARIZE_ACTIVITIES),
        Worker(client, task_queue=TTS_QUEUE, workflows=[], activities=TTS_ACTIVITIES),
        Worker(client, task_queue=CPU_QUEUE, workflows=[], activities=CPU_ACTIVITIES + SEPARATION_ACTIVITIES),
    ]
    logger.info(
        "starting %d workers (project=%s, asr=%s, diarize=%s, tts=%s, cpu=%s)",
        len(workers),
        PROJECT_QUEUE,
        ASR_QUEUE,
        DIARIZE_QUEUE,
        TTS_QUEUE,
        CPU_QUEUE,
    )
    await asyncio.gather(*(w.run() for w in workers))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())