'''
Copyright 2019-Present The OpenUBA Platform Authors
dashboards api router
'''

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.dashboard_repository import DashboardRepository
from core.api_schemas.dashboards import (
    DashboardCreate, DashboardUpdate, DashboardResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/dashboards", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboards", "write"))
):
    '''
    create a new dashboard
    '''
    repo = DashboardRepository(db)
    dashboard = repo.create(
        name=dashboard_data.name,
        created_by=UUID(current_user["user_id"]),
        description=dashboard_data.description,
        layout=dashboard_data.layout
    )
    logger.info(f"dashboard created: {dashboard.id}")
    return dashboard


@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    published: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboards", "read"))
):
    '''
    list dashboards with optional filters
    '''
    repo = DashboardRepository(db)
    dashboards = repo.list_all(
        published=published,
        limit=limit,
        offset=offset
    )
    return dashboards


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboards", "read"))
):
    '''
    get dashboard by id
    '''
    repo = DashboardRepository(db)
    dashboard = repo.get_by_id(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="dashboard not found")
    return dashboard


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    dashboard_data: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboards", "write"))
):
    '''
    update dashboard fields
    '''
    repo = DashboardRepository(db)
    dashboard = repo.update(dashboard_id, **dashboard_data.dict(exclude_unset=True))
    if not dashboard:
        raise HTTPException(status_code=404, detail="dashboard not found")
    return dashboard


@router.delete("/dashboards/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboards", "write"))
):
    '''
    delete a dashboard
    '''
    repo = DashboardRepository(db)
    success = repo.delete(dashboard_id)
    if not success:
        raise HTTPException(status_code=404, detail="dashboard not found")
