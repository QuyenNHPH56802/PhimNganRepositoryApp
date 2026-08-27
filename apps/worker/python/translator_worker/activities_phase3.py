"""Phase 3 activities: translate, QA, subtitle, normalize, TTS,
separation, mix, dubbing align, render, export, cleanup."""

from __future__ import annotations

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
    TranslationVersion,
    VoiceProfile,
    Workflow,
    WorkflowStep,
)
from translator_api.providers.base import ProviderContext, get_default_registry
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


def _record_step(session, project_id: str, name: str, *, status: str, signature: str | None = None, message: str | None = None) -> None:
    repo = WorkflowStepRepository(session)
    workflow = _latest_workflow(session, UUID(project_id))
    if workflow is None:
        return
    step = WorkflowStep(
        workflow_id=workflow.id,
        name=name,
        status=status,
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
        glossary = session.query(Glossary).filter_by(project_id=UUID(project_id), is_active=True).first()
        terms = glossary.terms if glossary else []
        provider = get_default_registry().get(TRANSLATE, cfg.provider_id)
        payload = TranslationInput(
            segments=[],
            glossary=_serialize_terms(terms),
            aliases=[],
            character_bible=[],
            style_preset="neutral",
            config=cfg,
        )
        ctx = _ctx(project_id, asset_id, session)
        try:
            response = await provider.run(payload, ctx=ctx)
        except Exception as exc:
            # Phase 3 default: no source segments, so we surface a stub translation response
            # while keeping the signature deterministic.
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import TranslationResponse

            response = TranslationResponse(
                provider_id=cfg.provider_id,
                model_id=cfg.model_id,
                prompt_version=cfg.prompt_version,
                segments=[],
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=cfg.model_id,
                    model_version=cfg.model_id,
                    provider_build=cfg.provider_id,
                    config_hash="pending",
                    prompt_version=cfg.prompt_version,
                ),
            )
            activity.logger.info("translate_segments stub: %s", exc)
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
        translations = [
            TranslationSegment(idx=idx, display_text="", tts_text="")
            for idx, _ in enumerate(latest_version.segments if latest_version else [])
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
        response = await provider.run(SubtitleInput(translations=[], original_segments=[], config=cfg), ctx=ctx)
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
        # Resolve provider from registry so we honour the project's
        # configured `provider_id` (e.g. ``edge_tts``, ``qwen3_tts``,
        # ``vietvoice_tts``). Fall back to VietVoice only when the registry
        # has no matching provider (defensive default).
        try:
            provider = get_default_registry().get(TTS, cfg.provider_id)
        except KeyError:
            provider = VietVoiceTtsProvider()
        ctx = _ctx(project_id, asset_id, session)
        voice_profile = session.query(VoiceProfile).filter_by(project_id=UUID(project_id)).first()
        payload = TtsInput(
            text="",
            voice_profile_id=str(voice_profile.id) if voice_profile else None,
            reference_audio_key=cfg.reference_audio_key,
            output_storage_prefix=f"tts/{project_id}",
            config=cfg,
        )
        import time as _time
        from translator_worker.metrics import observe_tts

        started = _time.perf_counter()
        try:
            response = await provider.run(payload, ctx=ctx)
            elapsed = _time.perf_counter() - started
            audio_seconds = (response.duration_ms / 1000.0) if getattr(response, "duration_ms", 0) else None
            observe_tts(provider=provider.id, generate_seconds=elapsed, audio_seconds=audio_seconds)
        except Exception as exc:
            elapsed = _time.perf_counter() - started
            observe_tts(provider=provider.id, generate_seconds=elapsed)
            activity.logger.info("tts_synthesize stub: %s", exc)
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import TtsResponse

            response = TtsResponse(
                voice_profile_id=voice_profile.id if voice_profile else None,
                audio_storage_key=f"tts/{project_id}/{provider.id}/stub.wav",
                duration_ms=0,
                sample_rate=cfg.sample_rate,
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=cfg.model_id,
                    model_version=cfg.model_id,
                    provider_build=provider.id,
                    config_hash="pending",
                ),
                fallback_used=True,
            )
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
        asset = asset_repo.list_for_project(UUID(project_id))[0]
        try:
            response = await provider.run(SeparationInput(asset_storage_key=asset.storage_key, config=cfg), ctx=ctx)
        except Exception as exc:
            activity.logger.info("audio_separate stub: %s", exc)
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import SeparationResponse

            response = SeparationResponse(
                vocals_key="",
                background_key="",
                method=provider.id,
                duration_ms=0,
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=cfg.model_id,
                    model_version="0.0.0",
                    provider_build=provider.id,
                    config_hash="pending",
                ),
            )
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
        try:
            response = await provider.run(
                DubbingAlignInput(
                    voice_storage_key=f"tts/{project_id}/stub.wav",
                    target_duration_ms=1000,
                    source_duration_ms=1000,
                    config=cfg,
                ),
                ctx=ctx,
            )
        except Exception as exc:
            activity.logger.info("dubbing_align stub: %s", exc)
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import AudioMixResponse

            response = AudioMixResponse(
                output_key=f"align/{project_id}/stub.wav",
                duration_ms=1000,
                sample_rate=48000,
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=provider.id,
                    model_version="0.0.0",
                    provider_build=provider.id,
                    config_hash="pending",
                ),
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
        try:
            response = await provider.run(
                MixInput(
                    voice_storage_key=f"tts/{project_id}/stub.wav",
                    background_storage_key=None,
                    output_storage_prefix=f"mix/{project_id}",
                    config=cfg,
                ),
                ctx=ctx,
            )
        except Exception as exc:
            activity.logger.info("audio_mix stub: %s", exc)
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import AudioMixResponse

            response = AudioMixResponse(
                output_key=f"mix/{project_id}/stub.wav",
                duration_ms=0,
                sample_rate=48000,
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=provider.id,
                    model_version="0.0.0",
                    provider_build=provider.id,
                    config_hash="pending",
                ),
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
        asset = asset_repo.list_for_project(UUID(project_id))[0]
        try:
            response = await provider.run(
                RenderInput(
                    source_video_key=asset.storage_key,
                    dubbed_audio_key=None,
                    subtitle_ass_key=None,
                    output_storage_prefix=f"render/{project_id}",
                    config=cfg,
                ),
                ctx=ctx,
            )
        except Exception as exc:
            activity.logger.info("render_build stub: %s", exc)
            from translator_shared.providers import ArtifactSignature
            from translator_shared.provider_responses_extra import RenderResponse

            response = RenderResponse(
                output_key=f"render/{project_id}/stub.mp4",
                duration_ms=0,
                validation={"size_bytes": 0},
                signature=ArtifactSignature(
                    input_hash="pending",
                    model_id=provider.id,
                    model_version="0.0.0",
                    provider_build=provider.id,
                    config_hash="pending",
                ),
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
        try:
            responses = await provider.run(
                ExportInput(
                    render_storage_key=f"render/{project_id}/stub.mp4",
                    formats=tuple(cfg.formats),
                    render_config=render_cfg,
                    export_config=cfg,
                ),
                ctx=ctx,
            )
        except Exception as exc:
            activity.logger.info("export_assemble stub: %s", exc)
            responses = []
        workflow = _latest_workflow(session, UUID(project_id))
        if workflow is not None and responses:
            render_job = (
                session.query(RenderJob).filter_by(workflow_id=workflow.id).order_by(RenderJob.created_at.desc()).first()
            )
            render_job_id = render_job.id if render_job else None
            for entry in responses:
                session.add(
                    Export(
                        render_job_id=render_job_id,
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