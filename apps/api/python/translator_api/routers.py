"""FastAPI routers using Phase 2 repositories."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.models import Project, Workflow
from translator_api.providers.registry import bootstrap
from translator_api.providers.registry_constants import TRANSLATE
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
    ProviderConfigResponse,
    ProviderConfigUpsert,
    WorkflowStatusResponse,
    WorkflowStepResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
)
from translator_api.settings import get_settings
from translator_api.storage_pkg import LocalStorage, S3CompatibleStorage
from translator_api.temporal_client import get_temporal_client
from translator_shared.providers import StorageProviderId
from translator_shared.workflows import QualityMode, WorkflowStatus

bootstrap()

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse()


@router.get("/readyz", response_model=HealthResponse, tags=["meta"])
async def readyz() -> HealthResponse:
    return HealthResponse(status="ready")


@router.get("/projects", response_model=ProjectListResponse, tags=["projects"])
async def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    repo = ProjectRepository(db)
    items = repo.list()
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
        total=len(items),
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = Project(
        title=payload.title,
        owner_id=UUID(int=0),
        source_language=payload.source_language,
        target_language=payload.target_language,
        quality_mode=payload.quality_mode.value,
        language_profile=payload.language_profile,
        status=WorkflowStatus.DRAFT.value,
    )
    repo.add(project)
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
    project = ProjectRepository(db).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectResponse(
        id=project.id,
        title=project.title,
        quality_mode=QualityMode(project.quality_mode),
        status=WorkflowStatus(project.status),
        created_at=project.created_at,
    )


@router.post(
    "/projects/{project_id}/assets:presign",
    response_model=AssetPresignResponse,
    tags=["assets"],
)
async def presign_asset(project_id: UUID, payload: AssetPresignRequest) -> AssetPresignResponse:
    settings = get_settings()
    storage = LocalStorage() if StorageProviderId(settings.storage_provider_id) == StorageProviderId.LOCAL_FS else S3CompatibleStorage()
    asset_id = UUID(int=0)
    key = f"projects/{project_id}/assets/{asset_id}/raw/{payload.filename}"
    return AssetPresignResponse(**storage.presign_put(key, mime=payload.mime, expires_in=3600))


@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowTriggerResponse,
    tags=["workflows"],
)
async def trigger_workflow(project_id: UUID, payload: WorkflowTriggerRequest, db: Session = Depends(get_db)) -> WorkflowTriggerResponse:
    project = ProjectRepository(db).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    client = await get_temporal_client()
    workflow_id = f"project-{project_id}"
    quality_mode = payload.quality_mode.value if payload.quality_mode else project.quality_mode
    handle = await client.start_workflow(
        "ProjectWorkflow",
        args=[str(project_id), quality_mode],
        id=workflow_id,
        task_queue="project-queue",
    )

    workflow = Workflow(
        project_id=project_id,
        temporal_workflow_id=workflow_id,
        temporal_run_id=handle.result_run_id,
        quality_mode=quality_mode,
        status=WorkflowStatus.PROCESSING.value,
    )
    WorkflowRepository(db).add(workflow)
    db.commit()
    return WorkflowTriggerResponse(workflow_id=handle.id, run_id=handle.result_run_id)


@router.get(
    "/projects/{project_id}/workflows/{workflow_id}",
    response_model=WorkflowStatusResponse,
    tags=["workflows"],
)
async def get_workflow_status(project_id: UUID, workflow_id: str, db: Session = Depends(get_db)) -> WorkflowStatusResponse:
    workflow = WorkflowRepository(db).get(UUID(workflow_id))
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
    workflow = WorkflowRepository(db).get(UUID(workflow_id))
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


@router.put(
    "/projects/{project_id}/provider-configs",
    response_model=ProviderConfigResponse,
    tags=["providers"],
)
async def upsert_provider_config(
    project_id: UUID,
    payload: ProviderConfigUpsert,
    db: Session = Depends(get_db),
) -> ProviderConfigResponse:
    repo = ProviderConfigRepository(db)
    config = repo.add(_build_provider_config_row(project_id, payload))
    db.commit()
    db.refresh(config)
    return _provider_config_response(config)


@router.get(
    "/projects/{project_id}/provider-configs",
    response_model=list[ProviderConfigResponse],
    tags=["providers"],
)
async def list_provider_configs(
    project_id: UUID,
    kind: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProviderConfigResponse]:
    from sqlalchemy import select

    from translator_api.models import ProviderConfig

    stmt = select(ProviderConfig).where(
        (ProviderConfig.project_id == project_id) | (ProviderConfig.project_id.is_(None))
    )
    if kind:
        stmt = stmt.where(ProviderConfig.provider_kind == kind)
    rows = db.execute(stmt).scalars().all()
    return [_provider_config_response(row) for row in rows]


def _build_provider_config_row(project_id: UUID, payload: ProviderConfigUpsert):
    from translator_api.models import ProviderConfig

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

    return ProviderConfig(
        project_id=project_id,
        provider_kind=payload.provider_kind,
        provider_id=payload.provider_id,
        config=payload.config,
        is_active=payload.is_active,
    )


def _provider_config_response(row) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=row.id,
        provider_kind=row.provider_kind,
        provider_id=row.provider_id,
        config=row.config,
        is_active=row.is_active,
    )