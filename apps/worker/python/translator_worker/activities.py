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
    """Validate project and asset before expensive operations.
    
    Checks:
    - Asset exists and has storage_key
    - Storage object exists
    - File format is supported (video: mp4/mkv/avi/mov, audio: mp3/wav/flac)
    - Duration is reasonable (1s to 12 hours)
    - File size is reasonable (>0 bytes, <10GB)
    """
    activity.logger.info("validate_inputs project_id=%s asset_id=%s", project_id, asset_id)
    
    from uuid import UUID
    from translator_worker.deps import make_worker_session_factory, build_storage
    from translator_api.models import Asset, Project
    
    factory = make_worker_session_factory()
    session = factory()
    errors = []
    
    try:
        # Validate project exists
        project = session.get(Project, UUID(project_id))
        if not project:
            errors.append(f"Project {project_id} not found")
            return {
                "ok": False, 
                "errors": errors,
                "signature": _empty_signature("validate_inputs").model_dump()
            }
        
        # If asset_id provided, validate asset
        if asset_id:
            asset = session.get(Asset, UUID(asset_id))
            if not asset:
                errors.append(f"Asset {asset_id} not found")
            elif not asset.storage_key:
                errors.append(f"Asset {asset_id} has no storage_key")
            else:
                # Validate storage object exists
                storage = build_storage()
                try:
                    if not storage.exists(asset.storage_key):
                        errors.append(f"Storage object not found: {asset.storage_key}")
                except Exception as e:
                    activity.logger.warning(f"Failed to check storage existence: {e}")
                
                # Validate file format
                supported_video = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
                supported_audio = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}
                
                if asset.kind == "video":
                    ext = "." + asset.storage_key.rsplit(".", 1)[-1].lower() if "." in asset.storage_key else ""
                    if ext not in supported_video:
                        errors.append(f"Unsupported video format: {ext}. Supported: {', '.join(supported_video)}")
                elif asset.kind == "audio":
                    ext = "." + asset.storage_key.rsplit(".", 1)[-1].lower() if "." in asset.storage_key else ""
                    if ext not in supported_audio:
                        errors.append(f"Unsupported audio format: {ext}. Supported: {', '.join(supported_audio)}")
                
                # Validate duration (1 second to 12 hours)
                if asset.duration_ms is not None:
                    min_duration_ms = 1000  # 1 second
                    max_duration_ms = 12 * 60 * 60 * 1000  # 12 hours
                    if asset.duration_ms < min_duration_ms:
                        errors.append(f"Duration too short: {asset.duration_ms}ms (min: {min_duration_ms}ms)")
                    elif asset.duration_ms > max_duration_ms:
                        errors.append(f"Duration too long: {asset.duration_ms}ms (max: {max_duration_ms}ms / 12 hours)")
                
                # Validate file size (>0, <10GB)
                if asset.size is not None:
                    max_size = 10 * 1024 * 1024 * 1024  # 10GB
                    if asset.size <= 0:
                        errors.append(f"Invalid file size: {asset.size} bytes")
                    elif asset.size > max_size:
                        errors.append(f"File too large: {asset.size} bytes (max: {max_size} bytes / 10GB)")
        
        if errors:
            activity.logger.warning(f"Validation failed: {errors}")
            return {
                "ok": False,
                "errors": errors,
                "signature": _empty_signature("validate_inputs").model_dump()
            }
        
        activity.logger.info("Validation passed for project_id=%s asset_id=%s", project_id, asset_id)
        return {
            "ok": True,
            "errors": [],
            "signature": _empty_signature("validate_inputs").model_dump()
        }
    
    finally:
        session.close()


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
    activity.logger.warning("⚠️ STUB asr_transcribe executed (does NOT write to DB) - project_id=%s", project_id)
    activity.heartbeat("asr_transcribe running")
    return {"ok": True, "signature": _empty_signature("asr_transcribe").model_dump()}


@activity.defn(name="align_text")
async def align_text(project_id: str) -> dict:
    activity.logger.info("align_text project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("align_text").model_dump()}


@activity.defn(name="diarize_segments")
async def diarize_segments(project_id: str) -> dict:
    activity.logger.warning("⚠️ STUB diarize_segments executed (does NOT write to DB) - project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("diarize_segments").model_dump()}


@activity.defn(name="normalize_chinese")
async def normalize_chinese(project_id: str) -> dict:
    activity.logger.info("normalize_chinese project_id=%s", project_id)
    return {"ok": True, "signature": _empty_signature("normalize_chinese").model_dump()}


@activity.defn(name="translate_segments")
async def translate_segments(project_id: str) -> dict:
    activity.logger.warning("⚠️ STUB translate_segments executed (does NOT write to DB) - project_id=%s", project_id)
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
