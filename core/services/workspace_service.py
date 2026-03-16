'''
Copyright 2019-Present The OpenUBA Platform Authors
workspace service for managing workspace lifecycle
'''

import logging
import os
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from core.db.models import Workspace
from core.repositories.workspace_repository import WorkspaceRepository

logger = logging.getLogger(__name__)

# hardware tier resource definitions
# requests are kept low for local Kind clusters; limits allow burst
HARDWARE_TIERS = {
    "cpu-small": {
        "requests": {"cpu": "100m", "memory": "128Mi"},
        "limits": {"cpu": "500m", "memory": "1Gi"},
    },
    "cpu-large": {
        "requests": {"cpu": "250m", "memory": "512Mi"},
        "limits": {"cpu": "2", "memory": "4Gi"},
    },
    "gpu-small": {
        "requests": {"cpu": "500m", "memory": "1Gi"},
        "limits": {"cpu": "2", "memory": "4Gi", "nvidia.com/gpu": "1"},
    },
    "gpu-large": {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "4", "memory": "8Gi", "nvidia.com/gpu": "4"},
    },
}

# nodeport range for workspaces
NODE_PORT_START = int(os.getenv("WORKSPACE_NODE_PORT_START", "31200"))
NODE_PORT_END = int(os.getenv("WORKSPACE_NODE_PORT_END", "31209"))


class WorkspaceService:
    '''
    service for managing workspace lifecycle
    handles workspace creation, stopping, restarting, and deletion
    '''

    def __init__(self, db: Session):
        self.db = db
        self.repo = WorkspaceRepository(db)

    def launch_workspace(
        self,
        name: str,
        created_by: UUID,
        environment: str = "default",
        hardware_tier: str = "cpu-small",
        ide: str = "jupyterlab",
        timeout_hours: int = 24,
    ) -> Workspace:
        '''
        launch a new workspace
        creates the database record and prepares for k8s deployment
        '''
        # allocate nodeport
        node_port = self._allocate_node_port()

        # create workspace record
        workspace = self.repo.create(
            name=name,
            environment=environment,
            hardware_tier=hardware_tier,
            ide=ide,
            created_by=created_by,
            timeout_hours=timeout_hours,
        )

        # set allocated nodeport and access_url
        # access_url is set now so the frontend can start probing immediately
        base_url = os.getenv("WORKSPACE_ACCESS_BASE_URL", "http://localhost")
        access_url = f"{base_url}:{node_port}"
        workspace = self.repo.update(
            workspace.id,
            node_port=node_port,
            access_url=access_url,
            cr_name=f"uba-ws-{str(workspace.id)[:8]}",
        )

        logger.info(f"workspace launched: {workspace.id} at {access_url}")
        return workspace

    def stop_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        '''
        stop a running workspace
        '''
        from datetime import datetime
        workspace = self.repo.get_by_id(workspace_id)
        if not workspace:
            return None
        if workspace.status not in ("running", "pending"):
            return workspace

        workspace = self.repo.update(
            workspace_id,
            status="stopped",
            stopped_at=datetime.utcnow(),
        )
        logger.info(f"workspace stopped: {workspace_id}")
        return workspace

    def restart_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        '''
        restart a stopped workspace
        preserves access_url so frontend can start probing when pod is back
        '''
        workspace = self.repo.get_by_id(workspace_id)
        if not workspace:
            return None
        if workspace.status not in ("stopped", "failed"):
            return workspace

        workspace = self.repo.update(
            workspace_id,
            status="pending",
            stopped_at=None,
        )
        logger.info(f"workspace restart requested: {workspace_id}")
        return workspace

    def delete_workspace(self, workspace_id: UUID) -> bool:
        '''
        delete a workspace and its associated resources
        '''
        success = self.repo.delete(workspace_id)
        if success:
            logger.info(f"workspace deleted: {workspace_id}")
        return success

    def get_hardware_tier(self, tier_name: str) -> dict:
        '''
        get resource limits for a hardware tier
        '''
        return HARDWARE_TIERS.get(tier_name, HARDWARE_TIERS["cpu-small"])

    def _allocate_node_port(self) -> int:
        '''
        allocate an available nodeport from the workspace range
        '''
        used_ports = set()
        workspaces = self.repo.list_all(limit=200)
        for ws in workspaces:
            # reserve ports for all non-deleted workspaces to avoid conflicts
            # when a stopped workspace is restarted and needs its port back
            if ws.node_port:
                used_ports.add(ws.node_port)

        for port in range(NODE_PORT_START, NODE_PORT_END + 1):
            if port not in used_ports:
                return port

        raise RuntimeError("no available nodeports in workspace range")
