'''
Copyright 2019-Present The OpenUBA Platform Authors
workspaces api router
'''

import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.workspace_repository import WorkspaceRepository
from core.services.workspace_service import WorkspaceService
from core.api_schemas.workspaces import WorkspaceCreate, WorkspaceResponse
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

WORKSPACE_NAMESPACE = os.getenv("WORKSPACE_NAMESPACE", "openuba")


def _create_workspace_crd(workspace, repo: WorkspaceRepository) -> None:
    '''
    create UBAWorkspace custom resource so the operator provisions the pod
    if creation fails, mark the workspace as failed with the error message
    '''
    try:
        from kubernetes import client as k8s_client, config as k8s_config
        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()

        api = k8s_client.CustomObjectsApi()
        cr_name = workspace.cr_name or f"uba-ws-{str(workspace.id)[:8]}"
        body = {
            "apiVersion": "openuba.io/v1",
            "kind": "UBAWorkspace",
            "metadata": {
                "name": cr_name,
                "namespace": WORKSPACE_NAMESPACE,
            },
            "spec": {
                "name": workspace.name,
                "environment": workspace.environment or "default",
                "hardware_tier": workspace.hardware_tier or "cpu-small",
                "ide": workspace.ide or "jupyterlab",
                "created_by": str(workspace.created_by),
                "timeout_hours": workspace.timeout_hours or 24,
                "node_port": workspace.node_port,
            },
        }
        api.create_namespaced_custom_object(
            group="openuba.io",
            version="v1",
            namespace=WORKSPACE_NAMESPACE,
            plural="ubaworkspaces",
            body=body,
        )
        logger.info(f"created UBAWorkspace CRD: {cr_name}")
    except Exception as e:
        logger.error(f"failed to create workspace CRD: {e}")
        repo.update(workspace.id, status="failed", error_message=str(e))


@router.post("/workspaces/launch", response_model=WorkspaceResponse, status_code=201)
async def launch_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "write"))
):
    '''
    launch a new workspace (create record, allocate nodeport, create CRD)
    '''
    svc = WorkspaceService(db)
    workspace = svc.launch_workspace(
        name=workspace_data.name,
        environment=workspace_data.environment,
        hardware_tier=workspace_data.hardware_tier,
        ide=workspace_data.ide,
        created_by=UUID(current_user["user_id"]),
        timeout_hours=workspace_data.timeout_hours,
    )

    # create the CRD so the operator provisions the pod
    repo = WorkspaceRepository(db)
    _create_workspace_crd(workspace, repo)

    logger.info(f"workspace launched: {workspace.id}")
    return workspace


@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(
    status: Optional[str] = Query(None, pattern="^(pending|starting|running|stopping|stopped|failed)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "read"))
):
    '''
    list workspaces with optional filters
    '''
    repo = WorkspaceRepository(db)
    workspaces = repo.list_all(
        status=status,
        limit=limit,
        offset=offset
    )

    # sync CRD status for any pending/creating workspaces so the list
    # reflects real-time operator progress without requiring a detail page visit
    for i, ws in enumerate(workspaces):
        if ws.status in ("pending", "creating") and ws.cr_name:
            workspaces[i] = _sync_workspace_crd_status(ws, repo)

    return workspaces


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "read"))
):
    '''
    get workspace by id
    syncs CRD status with DB if workspace is in a transitional state
    '''
    repo = WorkspaceRepository(db)
    workspace = repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")

    # sync CRD status → DB for pending/creating workspaces
    if workspace.status in ("pending", "creating") and workspace.cr_name:
        workspace = _sync_workspace_crd_status(workspace, repo)

    return workspace


def _sync_workspace_crd_status(workspace, repo: WorkspaceRepository):
    '''
    read workspace CRD status and sync to DB
    this lets the frontend see when a workspace transitions to running
    '''
    try:
        from kubernetes import client as k8s_client, config as k8s_config
        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()

        api = k8s_client.CustomObjectsApi()
        cr = api.get_namespaced_custom_object(
            group="openuba.io",
            version="v1",
            namespace=WORKSPACE_NAMESPACE,
            plural="ubaworkspaces",
            name=workspace.cr_name,
        )
        cr_status = cr.get("status", {})
        cr_phase = cr_status.get("phase", "").lower()

        if cr_phase == "running" and workspace.status != "running":
            workspace = repo.update(
                workspace.id,
                status="running",
                pod_name=cr_status.get("pod_name"),
                service_name=cr_status.get("service_name"),
                pvc_name=cr_status.get("pvc_name"),
                access_url=cr_status.get("access_url", workspace.access_url),
                node_port=cr_status.get("node_port", workspace.node_port),
            )
        elif cr_phase == "failed" and workspace.status != "failed":
            workspace = repo.update(
                workspace.id,
                status="failed",
            )
    except Exception as e:
        logger.debug(f"could not sync CRD status for {workspace.cr_name}: {e}")

    return workspace


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "write"))
):
    '''
    delete a workspace
    '''
    repo = WorkspaceRepository(db)
    success = repo.delete(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="workspace not found")


@router.post("/workspaces/{workspace_id}/stop", response_model=WorkspaceResponse)
async def stop_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "write"))
):
    '''
    stop a workspace (set status to stopped, set stopped_at)
    '''
    repo = WorkspaceRepository(db)
    workspace = repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")
    if workspace.status == "stopped":
        raise HTTPException(status_code=400, detail="workspace is already stopped")

    workspace = repo.update(
        workspace_id,
        status="stopped",
        stopped_at=datetime.utcnow()
    )
    logger.info(f"workspace stopped: {workspace_id}")
    return workspace


@router.post("/workspaces/{workspace_id}/restart", response_model=WorkspaceResponse)
async def restart_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("workspaces", "write"))
):
    '''
    restart a workspace (set status to pending, clear stopped_at)
    '''
    repo = WorkspaceRepository(db)
    workspace = repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")
    if workspace.status not in ("stopped", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"workspace must be stopped or failed to restart, current status: {workspace.status}"
        )

    workspace = repo.update(
        workspace_id,
        status="pending",
        stopped_at=None
    )
    logger.info(f"workspace restarted: {workspace_id}")
    return workspace
