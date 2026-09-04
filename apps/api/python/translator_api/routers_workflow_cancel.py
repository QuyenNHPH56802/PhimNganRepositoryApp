"""Workflow cancellation endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from translator_api.db import get_db
from translator_api.auth_dependency import get_identity
from translator_api.security.identity import UserIdentity
from translator_api.security.rbac import Role, require_project_role
from translator_api.repositories.workflow_repository import WorkflowRepository
from translator_api.temporal_client import get_temporal_client
from translator_shared.workflows import WorkflowStatus
import logging

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)


@router.post("/{workflow_id}/cancel", tags=["workflows"])
async def cancel_workflow(
    workflow_id: str,
    identity: UserIdentity = Depends(get_identity),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel a running workflow.
    
    Args:
        workflow_id: Workflow UUID, temporal_workflow_id, or temporal_run_id
    
    Returns:
        {"ok": true, "message": "Workflow cancelled"}
    """
    try:
        # Try to find workflow by UUID first
        workflow_uuid = UUID(workflow_id)
        workflow = WorkflowRepository(db).get(workflow_uuid)
    except (ValueError, TypeError):
        # Try to find by temporal IDs
        from sqlalchemy import select, or_
        from translator_api.models import Workflow
        
        stmt = select(Workflow).where(
            or_(
                Workflow.temporal_workflow_id == workflow_id,
                Workflow.temporal_run_id == workflow_id,
            )
        ).order_by(Workflow.started_at.desc())
        workflow = db.execute(stmt).scalars().first()
    
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    
    # Check permissions - user must have editor role on the project
    require_project_role(workflow.project_id, Role.EDITOR, db=db, identity=identity)
    
    # Check if workflow is already completed or cancelled
    if workflow.status in {WorkflowStatus.COMPLETED.value, WorkflowStatus.CANCELLED.value, WorkflowStatus.FAILED.value}:
        return {
            "ok": False,
            "message": f"Workflow already {workflow.status}",
            "status": workflow.status
        }
    
    # Cancel the Temporal workflow
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow.temporal_workflow_id)
        await handle.cancel()
        
        # Update workflow status in database
        workflow.status = WorkflowStatus.CANCELLED.value
        db.commit()
        
        logger.info(f"Cancelled workflow {workflow_id} for project {workflow.project_id}")
        
        return {
            "ok": True,
            "message": "Workflow cancelled successfully",
            "workflow_id": str(workflow.id),
            "temporal_workflow_id": workflow.temporal_workflow_id,
        }
    
    except Exception as e:
        logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel workflow: {str(e)}"
        )
