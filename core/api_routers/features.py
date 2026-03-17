'''
Copyright 2019-Present The OpenUBA Platform Authors
features api router
'''

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.feature_repository import FeatureRepository
from core.api_schemas.features import (
    FeatureGroupCreate, FeatureGroupResponse,
    FeatureCreate, FeatureResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/features/groups", response_model=FeatureGroupResponse, status_code=201)
async def create_feature_group(
    group_data: FeatureGroupCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "write"))
):
    '''
    create a new feature group
    '''
    repo = FeatureRepository(db)
    # check if group name already exists
    existing = repo.get_group_by_name(group_data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"feature group '{group_data.name}' already exists"
        )
    group = repo.create_group(
        name=group_data.name,
        created_by=UUID(current_user["user_id"]),
        description=group_data.description,
        entity=group_data.entity
    )
    logger.info(f"feature group created: {group.id}")
    return group


@router.get("/features/groups", response_model=List[FeatureGroupResponse])
async def list_feature_groups(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "read"))
):
    '''
    list all feature groups
    '''
    repo = FeatureRepository(db)
    groups = repo.list_groups()
    return groups


@router.get("/features/groups/{group_id}", response_model=FeatureGroupResponse)
async def get_feature_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "read"))
):
    '''
    get feature group by id
    '''
    repo = FeatureRepository(db)
    group = repo.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="feature group not found")
    return group


@router.get("/features/groups/name/{name}", response_model=FeatureGroupResponse)
async def get_feature_group_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "read"))
):
    '''
    get feature group by name
    '''
    repo = FeatureRepository(db)
    group = repo.get_group_by_name(name)
    if not group:
        raise HTTPException(status_code=404, detail="feature group not found")
    return group


@router.delete("/features/groups/{group_id}", status_code=204)
async def delete_feature_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "write"))
):
    '''
    delete a feature group
    '''
    repo = FeatureRepository(db)
    success = repo.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="feature group not found")


@router.post("/features/groups/{group_id}/features", response_model=FeatureResponse, status_code=201)
async def add_feature(
    group_id: UUID,
    feature_data: FeatureCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "write"))
):
    '''
    add a feature to a feature group
    '''
    repo = FeatureRepository(db)
    feature = repo.add_feature(
        group_id=group_id,
        name=feature_data.name,
        dtype=feature_data.dtype,
        transform=feature_data.transform,
        transform_params=feature_data.transform_params
    )
    if not feature:
        raise HTTPException(status_code=404, detail="feature group not found")
    logger.info(f"feature added to group {group_id}: {feature.id}")
    return feature


@router.get("/features/groups/{group_id}/features", response_model=List[FeatureResponse])
async def list_features(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("features", "read"))
):
    '''
    list all features in a feature group
    '''
    repo = FeatureRepository(db)
    group = repo.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="feature group not found")
    features = repo.get_features(group_id)
    return features
