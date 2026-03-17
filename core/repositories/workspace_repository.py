'''
Copyright 2019-Present The OpenUBA Platform Authors
workspace repository for database operations
'''

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Workspace


class WorkspaceRepository:
    '''
    repository for workspace database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        environment: str,
        hardware_tier: str,
        ide: str,
        created_by: UUID,
        timeout_hours: int = 24
    ) -> Workspace:
        '''
        create a new workspace record
        '''
        workspace = Workspace(
            name=name,
            environment=environment,
            hardware_tier=hardware_tier,
            ide=ide,
            created_by=created_by,
            timeout_hours=timeout_hours
        )
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        logging.info(f"created workspace: {workspace.id}")
        return workspace

    def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        '''
        get workspace by id
        '''
        return self.db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def list_all(
        self,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Workspace]:
        '''
        list all workspaces with optional filters
        '''
        query = self.db.query(Workspace)
        if status:
            query = query.filter(Workspace.status == status)
        if created_by:
            query = query.filter(Workspace.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, workspace_id: UUID, **kwargs) -> Optional[Workspace]:
        '''
        update workspace fields
        '''
        workspace = self.get_by_id(workspace_id)
        if not workspace:
            return None
        for key, value in kwargs.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        self.db.commit()
        self.db.refresh(workspace)
        logging.info(f"updated workspace: {workspace_id}")
        return workspace

    def delete(self, workspace_id: UUID) -> bool:
        '''
        delete a workspace
        '''
        workspace = self.get_by_id(workspace_id)
        if not workspace:
            return False
        self.db.delete(workspace)
        self.db.commit()
        logging.info(f"deleted workspace: {workspace_id}")
        return True
