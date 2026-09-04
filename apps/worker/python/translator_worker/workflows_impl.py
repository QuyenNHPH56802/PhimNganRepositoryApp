"""Workflows.

Phase 3 wires each activity onto its semantic task queue:
- asr-queue: asr_transcribe
- diarize-queue: diarize_segments
- tts-queue: tts_synthesize
- cpu-queue: every other activity

Workflows dispatch via start_activity with explicit task_queue + retry.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

from translator_shared.workflows import QualityMode
from translator_worker.constants import PROJECT_QUEUE
from translator_worker.retry import (
    DEFAULT_RETRY,
    LONG_RETRY,
    QA_NO_RETRY,
    SHORT_RETRY,
)

ASR_QUEUE = "asr-queue"
DIARIZE_QUEUE = "diarize-queue"
TTS_QUEUE = "tts-queue"
CPU_QUEUE = "cpu-queue"


def _start(activity_name: str, project_id: str, queue: str, retry_policy, *extra: str):
    args = [project_id, *extra]
    return workflow.start_activity(
        activity_name,
        args=list(args),
        start_to_close_timeout=timedelta(minutes=15),
        retry_policy=retry_policy,
        task_queue=queue,
    )


@workflow.defn(name="ProjectWorkflow")
class ProjectWorkflow:
    @workflow.run
    async def run(self, project_id: str, quality_mode: str | None) -> str:
        mode = QualityMode(quality_mode) if quality_mode else QualityMode.BALANCED
        await _start("validate_inputs", project_id, CPU_QUEUE, SHORT_RETRY, None)
        await _start("detect_subtitle_stream", project_id, CPU_QUEUE, SHORT_RETRY)
        await _start("analyze_media", project_id, CPU_QUEUE, SHORT_RETRY)
        await _start("chunk_plan", project_id, CPU_QUEUE, SHORT_RETRY)

        if mode == QualityMode.FAST:
            await workflow.execute_child_workflow(
                SubtitleWorkflow.run,
                args=[project_id],
                id=f"subtitle-{project_id}",
                task_queue=PROJECT_QUEUE,
            )
        else:
            await workflow.execute_child_workflow(
                DubbingWorkflow.run,
                args=[project_id, mode.value],
                id=f"dubbing-{project_id}",
                task_queue=PROJECT_QUEUE,
            )

        await _start("render_build", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("export_assemble", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("cleanup_orphans", project_id, CPU_QUEUE, SHORT_RETRY)
        return "ok"


@workflow.defn(name="SubtitleWorkflow")
class SubtitleWorkflow:
    @workflow.run
    async def run(self, project_id: str) -> str:
        await _start("asr_transcribe", project_id, ASR_QUEUE, DEFAULT_RETRY)
        await _start("align_text", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("diarize_segments", project_id, DIARIZE_QUEUE, DEFAULT_RETRY)
        await _start("normalize_chinese", project_id, CPU_QUEUE, SHORT_RETRY)
        await _start("translate_segments", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("translation_qa", project_id, CPU_QUEUE, QA_NO_RETRY)
        await _start("subtitle_segment", project_id, CPU_QUEUE, DEFAULT_RETRY)
        return "ok"


@workflow.defn(name="DubbingWorkflow")
class DubbingWorkflow:
    @workflow.run
    async def run(self, project_id: str, quality_mode: str) -> str:
        mode = QualityMode(quality_mode)
        await _start("asr_transcribe", project_id, ASR_QUEUE, DEFAULT_RETRY)
        await _start("align_text", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("diarize_segments", project_id, DIARIZE_QUEUE, DEFAULT_RETRY)
        await _start("normalize_chinese", project_id, CPU_QUEUE, SHORT_RETRY)
        await _start("translate_segments", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("translation_qa", project_id, CPU_QUEUE, QA_NO_RETRY)
        await _start("subtitle_segment", project_id, CPU_QUEUE, DEFAULT_RETRY)
        if mode == QualityMode.HIGH:
            await _start("audio_separate", project_id, CPU_QUEUE, LONG_RETRY)
        await _start("tts_synthesize", project_id, TTS_QUEUE, DEFAULT_RETRY)
        await _start("dubbing_align", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("audio_mix", project_id, CPU_QUEUE, DEFAULT_RETRY)
        return "ok"


@workflow.defn(name="ChunkWorkflow")
class ChunkWorkflow:
    @workflow.run
    async def run(self, project_id: str, start_ms: int, end_ms: int) -> str:
        await _start("asr_transcribe", project_id, ASR_QUEUE, DEFAULT_RETRY)
        await _start("translate_segments", project_id, CPU_QUEUE, DEFAULT_RETRY)
        await _start("tts_synthesize", project_id, TTS_QUEUE, DEFAULT_RETRY)
        return f"chunk-{start_ms}-{end_ms}"
