'''
Copyright 2019-Present The OpenUBA Platform Authors
experiments api router
'''

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.experiment_repository import ExperimentRepository
from core.api_schemas.experiments import (
    ExperimentCreate, ExperimentResponse,
    ExperimentRunCreate, ExperimentRunResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    experiment_data: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    create a new experiment
    '''
    repo = ExperimentRepository(db)
    experiment = repo.create(
        name=experiment_data.name,
        created_by=UUID(current_user["user_id"]),
        description=experiment_data.description
    )
    logger.info(f"experiment created: {experiment.id}")
    return experiment


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    list all experiments
    '''
    repo = ExperimentRepository(db)
    experiments = repo.list_all()
    return experiments


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    get experiment by id
    '''
    repo = ExperimentRepository(db)
    experiment = repo.get_by_id(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="experiment not found")
    return experiment


@router.delete("/experiments/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    delete an experiment
    '''
    repo = ExperimentRepository(db)
    success = repo.delete(experiment_id)
    if not success:
        raise HTTPException(status_code=404, detail="experiment not found")


@router.post("/experiments/{experiment_id}/runs", response_model=ExperimentRunResponse, status_code=201)
async def add_experiment_run(
    experiment_id: UUID,
    run_data: ExperimentRunCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    add a run to an experiment
    '''
    repo = ExperimentRepository(db)
    experiment = repo.get_by_id(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="experiment not found")

    run = repo.add_run(
        experiment_id=experiment_id,
        created_by=UUID(current_user["user_id"]),
        job_id=run_data.job_id,
        model_id=run_data.model_id,
        parameters=run_data.parameters,
        metrics=run_data.metrics
    )
    logger.info(f"experiment run added: {run.id} to experiment {experiment_id}")
    return run


@router.get("/experiments/{experiment_id}/runs", response_model=List[ExperimentRunResponse])
async def list_experiment_runs(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    list all runs for an experiment
    '''
    repo = ExperimentRepository(db)
    experiment = repo.get_by_id(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="experiment not found")
    runs = repo.get_runs(experiment_id)
    return runs


@router.patch("/experiments/runs/{run_id}", response_model=ExperimentRunResponse)
async def update_experiment_run(
    run_id: UUID,
    run_data: ExperimentRunCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    update an experiment run (e.g. update metrics or status)
    '''
    repo = ExperimentRepository(db)
    run = repo.update_run(
        run_id=run_id,
        **run_data.dict(exclude_unset=True)
    )
    if not run:
        raise HTTPException(status_code=404, detail="experiment run not found")
    logger.info(f"experiment run updated: {run_id}")
    return run


@router.get("/experiments/{experiment_id}/compare", response_model=List[ExperimentRunResponse])
async def compare_experiment_runs(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    compare experiment runs by returning all runs with their metrics
    '''
    repo = ExperimentRepository(db)
    experiment = repo.get_by_id(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="experiment not found")
    runs = repo.get_runs(experiment_id)
    return runs
