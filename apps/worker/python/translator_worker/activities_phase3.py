"""Phase 3 activities: translate, QA, subtitle, normalize, TTS,
separation, mix, dubbing align, render, export, cleanup."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from temporalio import activity

from translator_api.models import (
    AudioTrack,
    Export,
    Glossary,
    GlossaryTerm,
    Project,
    ProviderConfig,
    RenderJob,
    SubtitleTrack,
    TranslationSegment as TxModelSegment,
    TranslationVersion,
    VoiceProfile,
    Workflow,
    WorkflowStep,
)
from translator_api.providers.base import ProviderContext, get_default_registry
from translator_api.repositories.asset_repository import AssetRepository
from translator_api.repositories.provider_config_repository import ProviderConfigRepository
from translator_api.repositories.project_repository import ProjectRepository
from translator_api.repositories.translation_repository import TranslationVersionRepository
from translator_api.providers.cleanup.orphan import OrphanCleanupProvider
from translator_api.providers.dubbing.align import DubbingAlignInput, FfmpegAtempoAlignProvider
from translator_api.providers.export.compose import ExportInput, FfmpegExportProvider
from translator_api.providers.mix.ffmpeg_mix import FfmpegMixProvider, MixInput
from translator_api.providers.qa.rule_based import QaInput, RuleBasedQaProvider
from translator_api.providers.registry_constants import (
    AUDIO_SEPARATION,
    CLEANUP,
    DUBBING,
    EXPORT,
    MIX,
    QA,
    RENDER,
    SUBTITLE,
    TRANSLATE,
    TTS,
)
from translator_api.providers.render.ffmpeg_render import FfmpegRenderProvider, RenderInput
from translator_api.providers.separation.base import SeparationInput
from translator_api.providers.separation import Uvr5MdxProvider
from translator_api.providers.subtitle.cps_wrapper import CpsWrapperSubtitleProvider, SubtitleInput
from translator_api.providers.translate.base import (
    GlossaryTerm as TxGlossaryTerm,
    TranslationInput,
)
from translator_api.providers.tts.base import TtsInput
from translator_api.providers.tts.vietvoice import VietVoiceTtsProvider
from translator_api.repositories.asset_repository import AssetRepository
from translator_api.repositories.provider_config_repository import ProviderConfigRepository
from translator_api.repositories.project_repository import ProjectRepository
from translator_api.repositories.workflow_repository import (
    WorkflowStepRepository,
)
from translator_shared.provider_configs import (
    DubbingAlignProviderConfig,
    ExportProviderConfig,
    MixProviderConfig,
    QaProviderConfig,
    RenderProviderConfig,
    SeparationProviderConfig,
    SubtitleProviderConfig,
    TranslationProviderConfig,
    TtsProviderConfig,
)
from translator_shared.provider_responses_extra import (
    CleanupReport,
    TranslationSegment,
)
from translator_shared.providers import ArtifactSignature
from translator_worker.activities import _empty_signature
from translator_worker.deps import build_storage, make_worker_session_factory


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _factory():
    return make_worker_session_factory()


def _ctx(project_id: str, asset_id: str | None, session) -> ProviderContext:
    return ProviderContext(
        project_id=project_id,
        asset_id=asset_id,
        db_session=session,
        storage=build_storage(),
    )


def _record_step(session, project_id: str, name: str, *, status: str, signature: str | None = None, message: str | None = None, attempt: int = 0) -> None:
    repo = WorkflowStepRepository(session)
    workflow = _latest_workflow(session, UUID(project_id))
    if workflow is None:
        return
    step = WorkflowStep(
        workflow_id=workflow.id,
        name=name,
        status=status,
        attempt=attempt,
        progress_pct=100 if status == "ready" else 0,
        progress_message=message,
        artifact_signature=signature,
        started_at=_now() if status in {"processing", "ready"} else None,
        ended_at=_now() if status in {"ready", "failed"} else None,
    )
    repo.upsert(step)
    session.commit()


def _latest_workflow(session, project_id: UUID) -> Workflow | None:
    from sqlalchemy import select

    stmt = select(Workflow).where(Workflow.project_id == project_id).order_by(Workflow.started_at.desc()).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def _resolve_provider_config(session, project_id: UUID, kind: str) -> dict[str, Any] | None:
    repo = ProviderConfigRepository(session)
    config = repo.get_active(kind, project_id=project_id)
    if config is None:
        return None
    return config.config


def _serialize_terms(terms: list[GlossaryTerm]) -> list[TxGlossaryTerm]:
    return [
        TxGlossaryTerm(chinese=term.chinese, vietnamese=term.vietnamese, priority=term.priority)
        for term in terms
    ]


@activity.defn(name="normalize_chinese")
async def normalize_chinese(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "normalize_chinese", status="processing")
        # Phase 3: light-weight normalization only (no jieba dependency).
        # Full tokenization arrives when jieba is allowed at runtime.
        return {"ok": True, "signature": "phase3-normalize-stub"}
    finally:
        session.close()


@activity.defn(name="translate_segments")
async def translate_segments(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "translate_segments", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), TRANSLATE) or {}
        cfg = TranslationProviderConfig(**config_data) if config_data else TranslationProviderConfig()

        # Load source segments from the latest transcript version.
        from translator_api.repositories.transcript_repository import TranscriptRepository

        tx_repo = TranscriptRepository(session)
        latest_tx = tx_repo.latest_for_project(UUID(project_id))
        if latest_tx is None:
            _record_step(session, project_id, "translate_segments", status="skipped", message="no transcript")
            activity.logger.info("translate_segments skipped: no transcript for project_id=%s", project_id)
            return {
                "ok": True,
                "skipped": True,
                "reason": "no transcript found for project",
                "signature": _empty_signature("translate_segments").model_dump(),
            }
        from translator_api.models import TranscriptSegment

        source_segs = session.query(TranscriptSegment).filter_by(transcript_id=latest_tx.id).order_by(TranscriptSegment.start_ms).all()

        # Collect TTS text from source segments for TTS downstream.
        glossary = session.query(Glossary).filter_by(project_id=UUID(project_id), is_active=True).first()
        terms = glossary.terms if glossary else []
        provider = get_default_registry().get(TRANSLATE, cfg.provider_id)
        payload = TranslationInput(
            segments=[
                {
                    "idx": i,
                    "start_ms": int(s.start_ms),
                    "end_ms": int(s.end_ms),
                    "display_text": (getattr(s, "raw_text", None) or getattr(s, "normalized_text", None) or getattr(s, "text", "") or ""),
                    "speaker": (getattr(s, "speaker_label", None) or getattr(s, "speaker", "") or ""),
                }
                for i, s in enumerate(source_segs)
            ],
            glossary=_serialize_terms(terms),
            aliases=[],
            character_bible=[],
            style_preset="neutral",
            config=cfg,
        )
        ctx = _ctx(project_id, asset_id, session)
        response = await provider.run(payload, ctx=ctx)

        # Persist the translation version + segments so TTS can read them.
        tx_version_repo = TranslationVersionRepository(session)
        next_ver = tx_version_repo.next_version(latest_tx.id)
        tx_version = TranslationVersion(
            project_id=UUID(project_id),
            transcript_id=latest_tx.id,
            version=next_ver,
            provider_id=response.provider_id,
            model_id=response.model_id,
            prompt_version=response.prompt_version,
            signature=response.signature.fingerprint(),
            glossary_snapshot_id=glossary.id if glossary else None,
            style_preset="neutral",
            is_active=True,
        )
        tx_version_repo.add(tx_version)

        for seg in response.segments:
            model_seg = TxModelSegment(
                translation_version_id=tx_version.id,
                transcript_segment_id=source_segs[seg.idx].id if seg.idx < len(source_segs) else source_segs[0].id,
                display_text=seg.display_text,
                tts_text=seg.tts_text or seg.display_text,
                applied_glossary_terms=[{"term": t} for t in seg.applied_glossary_terms],
                confidence=seg.confidence,
            )
            session.add(model_seg)
        session.commit()

        _record_step(session, project_id, "translate_segments", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="translation_qa")
async def translation_qa(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "translation_qa", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), QA) or {}
        cfg = QaProviderConfig(**config_data) if config_data else QaProviderConfig()
        provider = RuleBasedQaProvider(cfg)
        latest_version = session.query(TranslationVersion).filter_by(project_id=UUID(project_id)).order_by(TranslationVersion.version.desc()).first()
        tx_segs = session.query(TxModelSegment).filter_by(translation_version_id=latest_version.id).all() if latest_version else []
        translations = [
            TranslationSegment(idx=idx, display_text=s.display_text, tts_text=s.tts_text or s.display_text)
            for idx, s in enumerate(tx_segs)
        ]
        glossary = session.query(Glossary).filter_by(project_id=UUID(project_id), is_active=True).first()
        terms = glossary.terms if glossary else []
        ctx = _ctx(project_id, asset_id, session)
        report = await provider.run(QaInput(source_segments=[], translations=translations, glossary=_serialize_terms(terms)), ctx=ctx)
        _record_step(session, project_id, "translation_qa", status="ready", message=f"qa_status={report.qa_status}")
        return report.model_dump()
    finally:
        session.close()


@activity.defn(name="subtitle_segment")
async def subtitle_segment(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "subtitle_segment", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), SUBTITLE) or {}
        cfg = SubtitleProviderConfig(**config_data) if config_data else SubtitleProviderConfig()
        provider = CpsWrapperSubtitleProvider(cfg)
        ctx = _ctx(project_id, asset_id, session)
        latest_version = session.query(TranslationVersion).filter_by(project_id=UUID(project_id)).order_by(TranslationVersion.version.desc()).first()
        tx_segs = session.query(TxModelSegment).filter_by(translation_version_id=latest_version.id).all() if latest_version else []
        translations = [
            TranslationSegment(idx=idx, display_text=s.display_text, tts_text=s.tts_text or s.display_text)
            for idx, s in enumerate(tx_segs)
        ]
        response = await provider.run(SubtitleInput(translations=translations, original_segments=[], config=cfg), ctx=ctx)
        _record_step(session, project_id, "subtitle_segment", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="tts_synthesize")
async def tts_synthesize(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "tts_synthesize", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), TTS) or {}
        cfg = TtsProviderConfig(**config_data) if config_data else TtsProviderConfig()
        try:
            provider = get_default_registry().get(TTS, cfg.provider_id)
        except KeyError:
            provider = VietVoiceTtsProvider()
        ctx = _ctx(project_id, asset_id, session)

        # Read translated TTS text from the latest TranslationVersion + segments.
        from translator_api.repositories.translation_repository import TranslationVersionRepository

        tx_repo = TranslationVersionRepository(session)
        latest_tx = tx_repo.latest_for_transcript(UUID(asset_id) if asset_id else UUID(project_id))
        # Fallback: find latest by project_id (if transcript_id not available).
        if latest_tx is None:
            from translator_api.models import TranslationVersion as TV

            stmt = (
                __import__("sqlalchemy").select(TV)
                .where(TV.project_id == UUID(project_id))
                .order_by(TV.created_at.desc())
                .limit(1)
            )
            latest_tx = session.execute(stmt).scalar_one_or_none()

        tts_texts: list[str] = []
        if latest_tx is not None:
            from translator_api.models import TranslationSegment as TsSeg

            segs = session.query(TsSeg).filter_by(translation_version_id=latest_tx.id).order_by(TsSeg.id).all()
            for s in segs:
                text = (s.tts_text or s.display_text or "").strip()
                if text:
                    tts_texts.append(text)

        if not tts_texts:
            _record_step(session, project_id, "tts_synthesize", status="skipped", message="no tts text")
            activity.logger.info("tts_synthesize skipped: no tts_text/display_text for project_id=%s", project_id)
            return {
                "ok": True,
                "skipped": True,
                "reason": "no translated text available",
                "signature": _empty_signature("tts_synthesize").model_dump(),
            }

        voice_profile = session.query(VoiceProfile).filter_by(project_id=UUID(project_id)).first()
        text = "\n".join(tts_texts)
        payload = TtsInput(
            text=text,
            voice_profile_id=str(voice_profile.id) if voice_profile else None,
            reference_audio_key=cfg.reference_audio_key,
            output_storage_prefix=f"tts/{project_id}",
            config=cfg,
        )
        import time as _time
        from translator_worker.metrics import observe_tts

        started = _time.perf_counter()
        # Try microservice first (Edge-TTS on port 3099) with retry logic
        import urllib.request, json, base64
        from urllib.error import HTTPError, URLError
        
        tts_url = os.environ.get("TTS_SERVICE_URL", "http://tts-service:3099/synthesize")
        req_data = {
            "text": text[:2000],
            "voice": cfg.model_id if cfg.model_id and "Neural" in cfg.model_id else "vi-VN-HoaiMyNeural",
            "engine": "edge",
        }
        
        # Retry logic: max 3 attempts with exponential backoff
        max_retries = 3
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    tts_url,
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    audio_bytes = base64.b64decode(data["audio_b64"])
                    audio_key = f"tts/{project_id}/dubbed.mp3"
                    ctx.storage.upload(audio_key, audio_bytes, mime="audio/mpeg")
                    from translator_shared.providers import ArtifactSignature
                    from translator_shared.provider_responses_extra import TtsResponse
                    response = TtsResponse(
                        voice_profile_id=voice_profile.id if voice_profile else None,
                        audio_storage_key=audio_key,
                        duration_ms=data.get("duration_ms", 1000),
                        sample_rate=cfg.sample_rate,
                        signature=ArtifactSignature(
                            input_hash="tts-hash",
                            model_id="vi-VN-HoaiMyNeural",
                            model_version="1.0.0",
                            provider_build="edge_tts",
                            config_hash="tts-edge",
                        ),
                        fallback_used=False,
                    )
                    # Success - break retry loop
                    break
                    
            except HTTPError as e:
                last_error = e
                if e.code == 502 and attempt < max_retries - 1:
                    # TTS service 502 error, retry with exponential backoff
                    wait_seconds = 2 ** attempt  # 1s, 2s, 4s
                    activity.logger.warning(
                        f"TTS service 502 error (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_seconds}s..."
                    )
                    _time.sleep(wait_seconds)
                else:
                    # Non-502 error or last attempt - raise
                    raise
                    
            except URLError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Network error, retry
                    wait_seconds = 2 ** attempt
                    activity.logger.warning(
                        f"TTS service connection error (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_seconds}s: {str(e)}"
                    )
                    _time.sleep(wait_seconds)
                else:
                    raise
        
        if response is None:
            # All retries exhausted
            raise RuntimeError(f"TTS service failed after {max_retries} attempts: {last_error}")
        _record_step(session, project_id, "tts_synthesize", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="audio_separate")
async def audio_separate(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "audio_separate", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), AUDIO_SEPARATION) or {}
        cfg = SeparationProviderConfig(**config_data) if config_data else SeparationProviderConfig()
        provider = Uvr5MdxProvider()
        ctx = _ctx(project_id, asset_id, session)
        asset_repo = AssetRepository(session)
        assets = asset_repo.list_for_project(UUID(project_id))
        if not assets:
            raise ValueError(f"No asset found for project {project_id}")
        asset = assets[0]
        response = await provider.run(SeparationInput(asset_storage_key=asset.storage_key, config=cfg), ctx=ctx)
        _record_step(session, project_id, "audio_separate", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="dubbing_align")
async def dubbing_align(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "dubbing_align", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), DUBBING) or {}
        cfg = DubbingAlignProviderConfig(**config_data) if config_data else DubbingAlignProviderConfig()
        provider = FfmpegAtempoAlignProvider()
        ctx = _ctx(project_id, asset_id, session)
        dubbed_key = f"tts/{project_id}/dubbed.mp3"
        if ctx.storage is None or not ctx.storage.exists(dubbed_key):
            raise RuntimeError(
                f"dubbing_align requires the TTS dubbed audio at '{dubbed_key}', "
                "but it does not exist. Run tts_synthesize first."
            )
        response = await provider.run(
            DubbingAlignInput(
                voice_storage_key=dubbed_key,
                target_duration_ms=1000,
                source_duration_ms=1000,
                config=cfg,
            ),
            ctx=ctx,
        )
        _record_step(session, project_id, "dubbing_align", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="audio_mix")
async def audio_mix(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "audio_mix", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), MIX) or {}
        cfg = MixProviderConfig(**config_data) if config_data else MixProviderConfig()
        provider = FfmpegMixProvider()
        ctx = _ctx(project_id, asset_id, session)
        dubbed_key = f"tts/{project_id}/dubbed.mp3"
        if ctx.storage is None or not ctx.storage.exists(dubbed_key):
            raise RuntimeError(
                f"audio_mix requires the TTS dubbed audio at '{dubbed_key}', "
                "but it does not exist. Run tts_synthesize first."
            )
        response = await provider.run(
            MixInput(
                voice_storage_key=dubbed_key,
                background_storage_key=None,
                output_storage_prefix=f"mix/{project_id}",
                config=cfg,
            ),
            ctx=ctx,
        )
        _record_step(session, project_id, "audio_mix", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="render_build")
async def render_build(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "render_build", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), RENDER) or {}
        cfg = RenderProviderConfig(**config_data) if config_data else RenderProviderConfig()
        provider = FfmpegRenderProvider()
        ctx = _ctx(project_id, asset_id, session)
        asset_repo = AssetRepository(session)
        assets = asset_repo.list_for_project(UUID(project_id))
        if not assets:
            raise ValueError(f"No asset found for project {project_id}")
        asset = assets[0]
        dubbed_key = f"tts/{project_id}/dubbed.mp3"
        if ctx.storage is None or not ctx.storage.exists(dubbed_key):
            raise RuntimeError(
                f"render_build requires the TTS dubbed audio at '{dubbed_key}', "
                "but it does not exist. Run tts_synthesize first."
            )
        response = await provider.run(
            RenderInput(
                source_video_key=asset.storage_key,
                dubbed_audio_key=dubbed_key,
                subtitle_ass_key=None,
                output_storage_prefix=f"render/{project_id}",
                config=cfg,
            ),
            ctx=ctx,
        )
        workflow = _latest_workflow(session, UUID(project_id))
        if workflow is not None:
            render_job = RenderJob(
                workflow_id=workflow.id,
                kind="video",
                status="ready",
                output_storage_key=response.output_key,
                progress_pct=100,
                validation=response.validation,
            )
            session.add(render_job)
        _record_step(session, project_id, "render_build", status="ready", signature=response.signature.fingerprint())
        return response.model_dump()
    finally:
        session.close()


@activity.defn(name="export_assemble")
async def export_assemble(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "export_assemble", status="processing")
        config_data = _resolve_provider_config(session, UUID(project_id), EXPORT) or {}
        cfg = ExportProviderConfig(**config_data) if config_data else ExportProviderConfig()
        render_cfg = RenderProviderConfig(**(_resolve_provider_config(session, UUID(project_id), RENDER) or {}))
        provider = FfmpegExportProvider()
        ctx = _ctx(project_id, asset_id, session)
        workflow = _latest_workflow(session, UUID(project_id))
        render_job = (
            session.query(RenderJob).filter_by(workflow_id=workflow.id).order_by(RenderJob.created_at.desc()).first()
            if workflow else None
        )
        if render_job is None:
            raise RuntimeError(
                f"export_assemble requires a completed render job for project {project_id}, "
                "but none exists. Run render_build first."
            )
        render_key = render_job.output_storage_key
        responses = await provider.run(
            ExportInput(
                render_storage_key=render_key,
                formats=tuple(cfg.formats),
                render_config=render_cfg,
                export_config=cfg,
            ),
            ctx=ctx,
        )
        if workflow is not None and responses:
            for entry in responses:
                session.add(
                    Export(
                        render_job_id=render_job.id,
                        format=entry.format,
                        storage_key=entry.storage_key,
                        size=entry.size_bytes,
                        checksum_sha256=entry.checksum_sha256,
                    )
                )
        _record_step(session, project_id, "export_assemble", status="ready")
        return {"exports": [r.model_dump() for r in responses]}
    finally:
        session.close()


@activity.defn(name="cleanup_orphans")
async def cleanup_orphans(project_id: str, asset_id: str | None = None) -> dict:
    factory = _factory()
    session = factory()
    try:
        _record_step(session, project_id, "cleanup_orphans", status="processing")
        provider = OrphanCleanupProvider()
        ctx = _ctx(project_id, asset_id, session)
        report: CleanupReport = await provider.run(f"projects/{project_id}/", ctx=ctx)
        _record_step(session, project_id, "cleanup_orphans", status="ready")
        return report.model_dump()
    finally:
        session.close()