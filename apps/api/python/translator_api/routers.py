"""FastAPI routers using Phase 2 repositories."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.models import Project, Workflow, Asset, AuditLog
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
    db.add(AuditLog(
        entity_type="project",
        entity_id=str(project.id),
        action="create",
        payload={"actor": identity.email, "title": payload.title},
    ))
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
async def presign_asset(
    project_id: UUID,
    payload: AssetPresignRequest,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> AssetPresignResponse:
    require_project_role(project_id, Role.EDITOR, db=db, identity=identity)
    settings = get_settings()
    storage = LocalStorage() if StorageProviderId(settings.storage_provider_id) == StorageProviderId.LOCAL_FS else S3CompatibleStorage()
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


@router.get(
    "/projects/{project_id}/provider-configs",
    response_model=list[ProviderConfigResponse],
    tags=["providers"],
)
async def list_provider_configs(
    project_id: UUID,
    kind: str | None = None,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> list[ProviderConfigResponse]:
    require_project_role(project_id, Role.VIEWER, db=db, identity=identity)
    repo = ProviderConfigRepository(db)
    rows = repo.list_for_project(project_id)
    if kind:
        rows = [r for r in rows if r.provider_kind == kind]
    return [_provider_config_response(row) for row in rows]


def _provider_config_response(row) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=row.id,
        provider_kind=row.provider_kind,
        provider_id=row.provider_id,
        config=row.config,
        is_active=row.is_active,
    )