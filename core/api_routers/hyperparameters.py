'''
Copyright 2019-Present The OpenUBA Platform Authors
hyperparameters api router
'''

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.hyperparameter_repository import HyperparameterRepository
from core.api_schemas.experiments import (
    HyperparameterSetCreate, HyperparameterSetResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/hyperparameters", response_model=HyperparameterSetResponse, status_code=201)
async def create_hyperparameter_set(
    hp_data: HyperparameterSetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    create a new hyperparameter set
    '''
    repo = HyperparameterRepository(db)
    hp_set = repo.create(
        name=hp_data.name,
        parameters=hp_data.parameters,
        created_by=UUID(current_user["user_id"]),
        model_id=hp_data.model_id,
        description=hp_data.description
    )
    logger.info(f"hyperparameter set created: {hp_set.id}")
    return hp_set


@router.get("/hyperparameters", response_model=List[HyperparameterSetResponse])
async def list_hyperparameter_sets(
    model_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    list hyperparameter sets with optional model_id filter
    '''
    repo = HyperparameterRepository(db)
    hp_sets = repo.list_all(model_id=model_id)
    return hp_sets


@router.get("/hyperparameters/{hp_id}", response_model=HyperparameterSetResponse)
async def get_hyperparameter_set(
    hp_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "read"))
):
    '''
    get hyperparameter set by id
    '''
    repo = HyperparameterRepository(db)
    hp_set = repo.get_by_id(hp_id)
    if not hp_set:
        raise HTTPException(status_code=404, detail="hyperparameter set not found")
    return hp_set


@router.put("/hyperparameters/{hp_id}", response_model=HyperparameterSetResponse)
async def update_hyperparameter_set(
    hp_id: UUID,
    hp_data: HyperparameterSetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    update hyperparameter set
    '''
    repo = HyperparameterRepository(db)
    hp_set = repo.update(
        hp_id,
        name=hp_data.name,
        parameters=hp_data.parameters,
        model_id=hp_data.model_id,
        description=hp_data.description
    )
    if not hp_set:
        raise HTTPException(status_code=404, detail="hyperparameter set not found")
    logger.info(f"hyperparameter set updated: {hp_id}")
    return hp_set


@router.delete("/hyperparameters/{hp_id}", status_code=204)
async def delete_hyperparameter_set(
    hp_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("experiments", "write"))
):
    '''
    delete a hyperparameter set
    '''
    repo = HyperparameterRepository(db)
    success = repo.delete(hp_id)
    if not success:
        raise HTTPException(status_code=404, detail="hyperparameter set not found")
