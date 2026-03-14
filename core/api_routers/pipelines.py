'''
Copyright 2019-Present The OpenUBA Platform Authors
pipelines api router
'''

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.pipeline_repository import PipelineRepository
from core.api_schemas.pipelines import (
    PipelineCreate, PipelineUpdate, PipelineResponse,
    PipelineRunResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/pipelines", response_model=PipelineResponse, status_code=201)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "write"))
):
    '''
    create a new pipeline
    '''
    repo = PipelineRepository(db)
    pipeline = repo.create(
        name=pipeline_data.name,
        steps=pipeline_data.steps,
        created_by=UUID(current_user["user_id"]),
        description=pipeline_data.description
    )
    logger.info(f"pipeline created: {pipeline.id}")
    return pipeline


@router.get("/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "read"))
):
    '''
    list all pipelines
    '''
    repo = PipelineRepository(db)
    pipelines = repo.list_all()
    return pipelines


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "read"))
):
    '''
    get pipeline by id
    '''
    repo = PipelineRepository(db)
    pipeline = repo.get_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return pipeline


@router.put("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    pipeline_data: PipelineUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "write"))
):
    '''
    update pipeline fields
    '''
    repo = PipelineRepository(db)
    pipeline = repo.update(pipeline_id, **pipeline_data.dict(exclude_unset=True))
    if not pipeline:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return pipeline


@router.delete("/pipelines/{pipeline_id}", status_code=204)
async def delete_pipeline(
    pipeline_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "write"))
):
    '''
    delete a pipeline
    '''
    repo = PipelineRepository(db)
    success = repo.delete(pipeline_id)
    if not success:
        raise HTTPException(status_code=404, detail="pipeline not found")


@router.post("/pipelines/{pipeline_id}/run", response_model=PipelineRunResponse, status_code=201)
async def run_pipeline(
    pipeline_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "write"))
):
    '''
    run a pipeline (creates a new pipeline run)
    '''
    repo = PipelineRepository(db)
    pipeline = repo.get_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="pipeline not found")

    pipeline_run = repo.create_run(
        pipeline_id=pipeline_id,
        created_by=UUID(current_user["user_id"])
    )
    logger.info(f"pipeline run created: {pipeline_run.id} for pipeline {pipeline_id}")
    return pipeline_run


@router.get("/pipelines/{pipeline_id}/runs", response_model=List[PipelineRunResponse])
async def list_pipeline_runs(
    pipeline_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "read"))
):
    '''
    list all runs for a pipeline
    '''
    repo = PipelineRepository(db)
    pipeline = repo.get_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="pipeline not found")
    runs = repo.list_runs(pipeline_id)
    return runs


@router.get("/pipelines/runs/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("pipelines", "read"))
):
    '''
    get pipeline run by id
    '''
    repo = PipelineRepository(db)
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="pipeline run not found")
    return run
