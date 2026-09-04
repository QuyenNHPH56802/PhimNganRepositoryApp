"""FastAPI routers using Phase 2 repositories."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.models import Project, Workflow, Asset, AuditLog, ProjectMember
from translator_api.providers.registry import bootstrap
from translator_api.providers.registry_constants import TRANSLATE
from translator_api.repositories.asset_repository import AssetRepository
from translator_api.repositories.provider_config_repository import ProviderConfigRepository
from translator_shared.locale import providers_for_pair, supported_pair
from translator_api.repositories.project_repository import ProjectRepository
from translator_api.repositories.workflow_repository import WorkflowRepository, WorkflowStepRepository
from translator_api.schemas import (
    AssetPresignRequest,
    AssetPresignResponse,
    HealthResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ProviderConfigResponse,
    ProviderConfigUpsert,
    WorkflowStatusResponse,
    WorkflowStepResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
)
logger = logging.getLogger(__name__)
from translator_api.settings import get_settings
from translator_api.storage_pkg import LocalStorage, S3CompatibleStorage
from translator_api.temporal_client import get_temporal_client
from translator_api.security.identity import UserIdentity
from translator_api.security.rbac import Role, require_project_role
from translator_shared.providers import StorageProviderId
from translator_shared.workflows import QualityMode, WorkflowStatus

bootstrap()

router = APIRouter()


from translator_api.auth_dependency import get_identity


@router.get("/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse()


@router.get("/readyz", response_model=HealthResponse, tags=["meta"])
async def readyz() -> HealthResponse:
    return HealthResponse(status="ready")


@router.get("/projects", response_model=ProjectListResponse, tags=["projects"])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> ProjectListResponse:
    """List projects with pagination support.
    
    Args:
        limit: Maximum number of projects to return (default: 50, max: 100)
        offset: Number of projects to skip (default: 0)
    """
    # Enforce max limit
    limit = min(limit, 100)
    
    repo = ProjectRepository(db)
    items = repo.list(limit=limit, offset=offset)
    
    # Get total count for pagination
    total = db.query(Project).count()
    
    return ProjectListResponse(
        items=[
            ProjectResponse(
                id=p.id,
                title=p.title,
                quality_mode=QualityMode(p.quality_mode),
                status=WorkflowStatus(p.status),
                created_at=p.created_at,
            )
            for p in items
        ],
        total=total,
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project(
    payload: ProjectCreate,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = Project(
        title=payload.title,
        owner_id=UUID(identity.user_id),
        source_language=payload.source_language,
        target_language=payload.target_language,
        quality_mode=payload.quality_mode.value,
        language_profile=payload.language_profile,
        status=WorkflowStatus.DRAFT.value,
    )
    repo.add(project)
    db.flush()  # Ensure project.id is populated for audit log FK references.
    
    # Add owner as project member (owner role)
    from datetime import datetime, timezone
    db.add(ProjectMember(
        project_id=project.id,
        user_id=UUID(identity.user_id),
        role="owner",
        added_at=datetime.now(timezone.utc),
    ))
    
    db.add(AuditLog(
        entity_type="project",
        entity_id=str(project.id),
        action="create",
        payload={"actor": identity.email, "title": payload.title},
    ))
    
    # Upsert TTS provider config if provided
    if payload.tts_provider_id:
        config_repo = ProviderConfigRepository(db)
        config_repo.upsert(
            project_id=project.id,
            provider_kind="tts",
            provider_id=payload.tts_provider_id,
            config=payload.tts_config or {},
            is_active=True,
        )
    
    # Upsert Translation provider config if provided
    if payload.translate_provider_id:
        config_repo = ProviderConfigRepository(db)
        config_repo.upsert(
            project_id=project.id,
            provider_kind="translate",
            provider_id=payload.translate_provider_id,
            config=payload.translate_config or {},
            is_active=True,
        )
    
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=project.id,
        title=project.title,
        quality_mode=QualityMode(project.quality_mode),
        status=WorkflowStatus(project.status),
        created_at=project.created_at,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
async def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectResponse:
    try:
        project_uuid = UUID(str(project_id))
    except (ValueError, TypeError):
        # Malformed UUID — surface as 404 rather than crashing with 500.
        raise HTTPException(status_code=404, detail="project not found")
    project = ProjectRepository(db).get(project_uuid)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectResponse(
        id=project.id,
        title=project.title,
        quality_mode=QualityMode(project.quality_mode),
        status=WorkflowStatus(project.status),
        created_at=project.created_at,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project metadata (currently only title)."""
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    
    # Update fields
    if payload.title is not None:
        project.title = payload.title
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        title=project.title,
        quality_mode=QualityMode(project.quality_mode),
        status=WorkflowStatus(project.status),
        created_at=project.created_at,
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
async def delete_project(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> None:
    """Delete a project and all associated data (assets, workflows, transcripts, etc.).

    Only the project owner may delete. The Temporal workflow (if running) is
    cancelled and local storage files for the project are removed.
    """
    require_project_role(project_id, Role.OWNER, db=db, identity=identity)
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    # Best-effort: cancel any running Temporal workflow for this project.
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(f"project-{project_id}")
        await handle.cancel()
    except Exception as e:
        logger.warning("Could not cancel workflow for project %s: %s", project_id, e)

    # Best-effort: delete local storage files belonging to this project.
    try:
        settings = get_settings()
        if (settings.storage_provider_id or "").lower() in {"local", "local_fs", "local_storage"}:
            storage = LocalStorage()
            asset_prefix = f"projects/{project_id}/"
            for asset in AssetRepository(db).list_for_project(project_id):
                if asset.storage_key:
                    try:
                        storage.delete(asset.storage_key)
                    except Exception as e:
                        logger.warning("Failed to delete asset %s: %s", asset.storage_key, e)
            # Remove the entire project directory tree as a safety net.
            from pathlib import Path
            project_dir = storage._root / f"projects/{project_id}"
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir, ignore_errors=True)
    except Exception as e:
        logger.warning("Storage cleanup failed for project %s: %s", project_id, e)

    # Audit before delete so the log keeps a record (project_id may become orphan,
    # which is acceptable for the audit trail).
    db.add(AuditLog(
        entity_type="project",
        entity_id=str(project.id),
        action="delete",
        payload={"actor": identity.email, "title": project.title},
    ))

    repo.delete(project)
    db.commit()


@router.post(
    "/projects/{project_id}/assets:presign",
    response_model=AssetPresignResponse,
    tags=["assets"],
)
async def presign_asset(
    project_id: UUID,
    payload: AssetPresignRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> AssetPresignResponse:
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    settings = get_settings()
    provider_str = (settings.storage_provider_id or "").lower()
    is_local = provider_str in {"local", "local_fs", "local_storage"}
    storage = LocalStorage() if is_local else S3CompatibleStorage()
    asset = Asset(
        project_id=project_id,
        kind="video",
        storage_key="",
        mime=payload.mime,
        size=payload.size,
        uploaded_by=UUID(identity.user_id),
    )
    AssetRepository(db).add(asset)
    db.commit()
    db.refresh(asset)
    key = f"projects/{project_id}/assets/{asset.id}/raw/{payload.filename}"
    asset.storage_key = key
    db.commit()
    return AssetPresignResponse(**storage.presign_put(key, mime=payload.mime, expires_in=3600))


from fastapi import File, UploadFile
from fastapi.responses import FileResponse


@router.post(
    "/projects/{project_id}/assets:upload",
    tags=["assets"],
)
async def upload_asset_direct(
    project_id: UUID,
    file: UploadFile = File(...),
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
):
    """Direct file upload for local storage mode (browser can't PUT to file:// URLs)."""
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    settings = get_settings()
    storage = LocalStorage()
    data = await file.read()
    asset = Asset(
        project_id=project_id,
        kind="video",
        storage_key="",
        mime=file.content_type or "application/octet-stream",
        size=len(data),
        uploaded_by=UUID(identity.user_id),
    )
    AssetRepository(db).add(asset)
    db.commit()
    db.refresh(asset)
    key = f"projects/{project_id}/assets/{asset.id}/raw/{file.filename}"
    asset.storage_key = key
    db.commit()
    storage.upload(key, data, mime=file.content_type or "application/octet-stream")
    return {"key": key, "asset_id": str(asset.id), "url": f"/local-assets/{key}"}


@router.get("/local-assets/{key:path}", tags=["assets"])
async def serve_local_asset(key: str):
    """Serve files from local storage so the browser can load uploaded videos."""
    settings = get_settings()
    storage = LocalStorage()
    from pathlib import Path
    file_path = storage._path(key)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # Guess content type from extension
    ext = file_path.suffix.lower()
    media_types = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
                   ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
                   ".srt": "text/plain", ".vtt": "text/vtt", ".json": "application/json"}
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(str(file_path), media_type=media_type)

@router.get(
    "/projects/{project_id}/workflows",
    response_model=list,
    tags=["workflows"],
)
async def list_workflows(
    project_id: UUID,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> list:
    project = ProjectRepository(db).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    require_project_role(project_id, Role.VIEWER, db=db, identity=identity)
    
    workflows = db.query(Workflow).filter(Workflow.project_id == project_id).order_by(Workflow.started_at.desc()).all()
    return [
        {
            "id": str(w.id),
            "status": w.status,
            "quality_mode": w.quality_mode,
            "started_at": w.started_at.isoformat() if w.started_at else None,
            "ended_at": w.ended_at.isoformat() if w.ended_at else None,
        }
        for w in workflows
    ]

@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowTriggerResponse,
    tags=["workflows"],
)
async def trigger_workflow(
    project_id: UUID,
    payload: WorkflowTriggerRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> WorkflowTriggerResponse:
    project = ProjectRepository(db).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)

    try:
        client = await get_temporal_client()
    except Exception as e:
        logger.error(f"Failed to connect to Temporal: {e}")
        raise HTTPException(status_code=503, detail="Workflow engine unavailable. Please try again later.")

    workflow_id = f"project-{project_id}"
    quality_mode = payload.quality_mode.value if payload.quality_mode else project.quality_mode

    try:
        handle = await client.start_workflow(
            "ProjectWorkflow",
            args=[str(project_id), quality_mode],
            id=workflow_id,
            task_queue="project-queue",
        )
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

    workflow = Workflow(
        project_id=project_id,
        temporal_workflow_id=workflow_id,
        temporal_run_id=handle.result_run_id,
        quality_mode=quality_mode,
        status=WorkflowStatus.PROCESSING.value,
    )
    WorkflowRepository(db).add(workflow)
    db.flush()
    db.add(AuditLog(
        entity_type="workflow",
        entity_id=str(workflow.id),
        action="trigger",
        payload={
            "actor": identity.email,
            "project_id": str(project_id),
            "quality_mode": quality_mode,
        },
    ))
    db.commit()
    return WorkflowTriggerResponse(workflow_id=handle.id, run_id=handle.result_run_id)


def _find_workflow(db: Session, project_id: UUID, workflow_id: str) -> Workflow | None:
    from sqlalchemy import select, or_
    try:
        wf_uuid = UUID(workflow_id)
        wf = WorkflowRepository(db).get(wf_uuid)
        if wf is not None:
            return wf
    except (ValueError, TypeError):
        pass
    stmt = (
        select(Workflow)
        .where(
            Workflow.project_id == project_id,
            or_(
                Workflow.temporal_workflow_id == workflow_id,
                Workflow.temporal_run_id == workflow_id,
            ),
        )
        .order_by(Workflow.started_at.desc())
    )
    return db.execute(stmt).scalars().first()


@router.get(
    "/projects/{project_id}/workflows/{workflow_id}",
    response_model=WorkflowStatusResponse,
    tags=["workflows"],
)
async def get_workflow_status(project_id: UUID, workflow_id: str, db: Session = Depends(get_db)) -> WorkflowStatusResponse:
    workflow = _find_workflow(db, project_id, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return WorkflowStatusResponse(
        workflow_id=workflow.temporal_workflow_id,
        run_id=workflow.temporal_run_id,
        status=WorkflowStatus(workflow.status),
        last_error=str(workflow.last_error) if workflow.last_error else None,
    )


@router.get(
    "/projects/{project_id}/workflows/{workflow_id}/steps",
    response_model=list[WorkflowStepResponse],
    tags=["workflows"],
)
async def list_workflow_steps(project_id: UUID, workflow_id: str, db: Session = Depends(get_db)) -> list[WorkflowStepResponse]:
    workflow = _find_workflow(db, project_id, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    steps = WorkflowStepRepository(db).list_for_workflow(workflow.id)
    return [
        WorkflowStepResponse(
            id=s.id,
            name=s.name,
            status=s.status,
            attempt=s.attempt,
            progress_pct=s.progress_pct,
            progress_message=s.progress_message,
            artifact_signature=s.artifact_signature,
        )
        for s in steps
    ]


@router.get(
    "/projects/{project_id}/provider-configs",
    response_model=list[ProviderConfigResponse],
    tags=["providers"],
)
async def list_project_provider_configs(
    project_id: UUID,
    kind: str | None = None,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> list[ProviderConfigResponse]:
    from sqlalchemy import select
    from translator_api.models import ProviderConfig
    require_project_role(project_id, Role.VIEWER, db=db, identity=identity)
    stmt = select(ProviderConfig).where(ProviderConfig.project_id == project_id)
    if kind:
        stmt = stmt.where(ProviderConfig.provider_kind == kind)
    rows = list(db.execute(stmt).scalars())
    return [_provider_config_response(row) for row in rows]


@router.put(
    "/projects/{project_id}/provider-configs",
    response_model=ProviderConfigResponse,
    tags=["providers"],
)
async def upsert_provider_config(
    project_id: UUID,
    payload: ProviderConfigUpsert,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    # Validate language pair constraints for translation providers before persisting.
    if payload.provider_kind == TRANSLATE:
        src = payload.config.get("source_language") if payload.config else None
        tgt = payload.config.get("target_language") if payload.config else None
        if src and tgt:
            if not supported_pair(src, tgt):
                raise HTTPException(status_code=422, detail=f"language pair {src}->{tgt} not supported")
            allowed = providers_for_pair(src, tgt)
            if payload.provider_id not in allowed:
                raise HTTPException(
                    status_code=422,
                    detail=f"provider {payload.provider_id} not allowed for {src}->{tgt}; allowed={sorted(allowed)}",
                )

    repo = ProviderConfigRepository(db)
    config = repo.upsert(
        project_id=project_id,
        provider_kind=payload.provider_kind,
        provider_id=payload.provider_id,
        config=payload.config,
        is_active=payload.is_active,
    )
    db.add(AuditLog(
        entity_type="provider_config",
        entity_id=str(config.id),
        action="upsert",
        payload={
            "actor": identity.email,
            "project_id": str(project_id),
            "provider_kind": payload.provider_kind,
            "provider_id": payload.provider_id,
        },
    ))
    db.commit()
    db.refresh(config)
    return _provider_config_response(config)


@router.put(
    "/system/provider-configs",
    response_model=ProviderConfigResponse,
    tags=["providers"],
)
async def upsert_global_provider_config(
    payload: ProviderConfigUpsert,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    repo = ProviderConfigRepository(db)
    config = repo.upsert(
        project_id=None,
        provider_kind=payload.provider_kind,
        provider_id=payload.provider_id,
        config=payload.config,
        is_active=payload.is_active,
    )
    db.add(AuditLog(
        entity_type="provider_config",
        entity_id=str(config.id),
        action="upsert_global",
        payload={
            "actor": identity.email,
            "provider_kind": payload.provider_kind,
            "provider_id": payload.provider_id,
        },
    ))
    db.commit()
    db.refresh(config)
    return _provider_config_response(config)


@router.get(
    "/system/provider-configs",
    response_model=list[ProviderConfigResponse],
    tags=["providers"],
)
async def list_global_provider_configs(
    kind: str | None = None,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> list[ProviderConfigResponse]:
    from sqlalchemy import select
    from translator_api.models import ProviderConfig
    stmt = select(ProviderConfig).where(ProviderConfig.project_id.is_(None))
    if kind:
        stmt = stmt.where(ProviderConfig.provider_kind == kind)
    rows = list(db.execute(stmt).scalars())
    return [_provider_config_response(row) for row in rows]


def _provider_config_response(row) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=row.id,
        provider_kind=row.provider_kind,
        provider_id=row.provider_id,
        config=row.config,
        is_active=row.is_active,
    )




# Duplicate endpoint removed - now handled by routers_providers.py
# @router.get("/providers/{kind}/metadata", response_model=dict, tags=["providers"])
# See: translator_api.routers_providers for the active implementation
