"""Activity stubs.

Phase 1 only registers no-op activities that return an empty ArtifactSignature
and log a checkpoint. Real provider integrations arrive in Phase 2+; see
docs/workflow.md for the activity inventory and retry policy table.
"""

from __future__ import annotations

from temporalio import activity

from translator_shared.providers import ArtifactSignature


def _empty_signature(stub: str) -> ArtifactSignature:
    return ArtifactSignature(
        input_hash="pending",
        model_id=stub,
        model_version="0.0.0",
        provider_build="phase1-stub",
        config_hash="pending",
    )


@activity.defn(name="validate_inputs")
async def validate_inputs(project_id: str, asset_id: str | None) -> dict:
    activity.logger.info("validate_inputs project_id=%s asset_id=%s", project_id, asset_id)
    return {"ok": True, "signature": _empty_signature("validate_inputs").model_dump()}


@activity.defn(name="detect_subtitle_stream")
async def detect_subtitle_stream(project_id: str) -> dict:
    activity.logger.info("detect_subtitle_stream project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("detect_subtitle_stream").model_dump()}


@activity.defn(name="analyze_media")
async def analyze_media(project_id: str) -> dict:
    activity.logger.info("analyze_media project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("analyze_media").model_dump()}


@activity.defn(name="chunk_plan")
async def chunk_plan(project_id: str) -> dict:
    activity.logger.info("chunk_plan project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("chunk_plan").model_dump()}


@activity.defn(name="asr_transcribe")
async def asr_transcribe(project_id: str) -> dict:
    activity.logger.info("asr_transcribe project_id=%s", project_id)
    activity.heartbeat("asr_transcribe running")
    return {"ok": True, "signature": _empty_signature("asr_transcribe").model_dump()}


@activity.defn(name="align_text")
async def align_text(project_id: str) -> dict:
    activity.logger.info("align_text project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("align_text").model_dump()}


@activity.defn(name="diarize_segments")
async def diarize_segments(project_id: str) -> dict:
    activity.logger.info("diarize_segments project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("diarize_segments").model_dump()}


@activity.defn(name="normalize_chinese")
async def normalize_chinese(project_id: str) -> dict:
    activity.logger.info("normalize_chinese project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("normalize_chinese").model_dump()}


@activity.defn(name="translate_segments")
async def translate_segments(project_id: str) -> dict:
    activity.logger.info("translate_segments project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("translate_segments").model_dump()}


@activity.defn(name="translation_qa")
async def translation_qa(project_id: str) -> dict:
    activity.logger.info("translation_qa project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("translation_qa").model_dump()}


@activity.defn(name="subtitle_segment")
async def subtitle_segment(project_id: str) -> dict:
    activity.logger.info("subtitle_segment project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("subtitle_segment").model_dump()}


@activity.defn(name="tts_synthesize")
async def tts_synthesize(project_id: str) -> dict:
    activity.logger.info("tts_synthesize project_id=%s", project_id)
    activity.heartbeat("tts_synthesize running")
    return {"ok": True, "signature": _empty_signature("tts_synthesize").model_dump()}


@activity.defn(name="audio_separate")
async def audio_separate(project_id: str) -> dict:
    activity.logger.info("audio_separate project_id=%s", project_id)
    activity.heartbeat("audio_separate running")
    return {"ok": True, "signature": _empty_signature("audio_separate").model_dump()}


@activity.defn(name="audio_mix")
async def audio_mix(project_id: str) -> dict:
    activity.logger.info("audio_mix project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("audio_mix").model_dump()}


@activity.defn(name="dubbing_align")
async def dubbing_align(project_id: str) -> dict:
    activity.logger.info("dubbing_align project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("dubbing_align").model_dump()}


@activity.defn(name="render_build")
async def render_build(project_id: str) -> dict:
    activity.logger.info("render_build project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("render_build").model_dump()}


@activity.defn(name="export_assemble")
async def export_assemble(project_id: str) -> dict:
    activity.logger.info("export_assemble project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("export_assemble").model_dump()}


@activity.defn(name="cleanup_orphans")
async def cleanup_orphans(project_id: str) -> dict:
    activity.logger.info("cleanup_orphans project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("cleanup_orphans").model_dump()}