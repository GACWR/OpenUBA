'''
Copyright 2019-Present The OpenUBA Platform Authors
visualizations api router
'''

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.visualization_repository import VisualizationRepository
from core.api_schemas.visualizations import (
    VisualizationCreate, VisualizationUpdate, VisualizationResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/visualizations", response_model=VisualizationResponse, status_code=201)
async def create_visualization(
    viz_data: VisualizationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "write"))
):
    '''
    create a new visualization
    '''
    repo = VisualizationRepository(db)
    visualization = repo.create(
        name=viz_data.name,
        backend=viz_data.backend,
        output_type=viz_data.output_type,
        created_by=UUID(current_user["user_id"]),
        description=viz_data.description,
        code=viz_data.code,
        data=viz_data.data,
        config=viz_data.config,
        refresh_interval=viz_data.refresh_interval
    )
    logger.info(f"visualization created: {visualization.id}")
    return visualization


@router.get("/visualizations", response_model=List[VisualizationResponse])
async def list_visualizations(
    published: Optional[bool] = Query(None),
    backend: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "read"))
):
    '''
    list visualizations with optional filters
    '''
    repo = VisualizationRepository(db)
    visualizations = repo.list_all(
        published=published,
        backend=backend,
        limit=limit,
        offset=offset
    )
    return visualizations


@router.get("/visualizations/{viz_id}", response_model=VisualizationResponse)
async def get_visualization(
    viz_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "read"))
):
    '''
    get visualization by id
    '''
    repo = VisualizationRepository(db)
    visualization = repo.get_by_id(viz_id)
    if not visualization:
        raise HTTPException(status_code=404, detail="visualization not found")
    return visualization


@router.put("/visualizations/{viz_id}", response_model=VisualizationResponse)
async def update_visualization(
    viz_id: UUID,
    viz_data: VisualizationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "write"))
):
    '''
    update visualization fields
    '''
    repo = VisualizationRepository(db)
    visualization = repo.update(viz_id, **viz_data.dict(exclude_unset=True))
    if not visualization:
        raise HTTPException(status_code=404, detail="visualization not found")
    return visualization


@router.delete("/visualizations/{viz_id}", status_code=204)
async def delete_visualization(
    viz_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "write"))
):
    '''
    delete a visualization
    '''
    repo = VisualizationRepository(db)
    success = repo.delete(viz_id)
    if not success:
        raise HTTPException(status_code=404, detail="visualization not found")


@router.post("/visualizations/{viz_id}/publish", response_model=VisualizationResponse)
async def publish_visualization(
    viz_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("visualizations", "write"))
):
    '''
    publish a visualization
    '''
    repo = VisualizationRepository(db)
    visualization = repo.get_by_id(viz_id)
    if not visualization:
        raise HTTPException(status_code=404, detail="visualization not found")
    if visualization.published:
        raise HTTPException(status_code=400, detail="visualization is already published")

    visualization = repo.update(viz_id, published=True)
    logger.info(f"visualization published: {viz_id}")
    return visualization
