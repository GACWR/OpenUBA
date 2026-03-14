'''
Copyright 2019-Present The OpenUBA Platform Authors
datasets api router
'''

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.dataset_repository import DatasetRepository
from core.api_schemas.datasets import (
    DatasetCreate, DatasetUpdate, DatasetResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/datasets", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data", "write"))
):
    '''
    create a new dataset
    '''
    repo = DatasetRepository(db)
    dataset = repo.create(
        name=dataset_data.name,
        created_by=UUID(current_user["user_id"]),
        description=dataset_data.description,
        source_type=dataset_data.source_type,
        format=dataset_data.format
    )
    logger.info(f"dataset created: {dataset.id}")
    return dataset


@router.get("/datasets", response_model=List[DatasetResponse])
async def list_datasets(
    source_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data", "read"))
):
    '''
    list datasets with optional filters
    '''
    repo = DatasetRepository(db)
    datasets = repo.list_all(
        source_type=source_type,
        limit=limit,
        offset=offset
    )
    return datasets


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data", "read"))
):
    '''
    get dataset by id
    '''
    repo = DatasetRepository(db)
    dataset = repo.get_by_id(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="dataset not found")
    return dataset


@router.patch("/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: UUID,
    dataset_data: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data", "write"))
):
    '''
    update dataset fields
    '''
    repo = DatasetRepository(db)
    dataset = repo.update(dataset_id, **dataset_data.dict(exclude_unset=True))
    if not dataset:
        raise HTTPException(status_code=404, detail="dataset not found")
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data", "write"))
):
    '''
    delete a dataset
    '''
    repo = DatasetRepository(db)
    success = repo.delete(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="dataset not found")
