'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class FeatureGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    entity: str = Field(default="default", max_length=100)


class FeatureCreate(BaseModel):
    group_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    dtype: Optional[str] = Field(None, max_length=50)
    transform: Optional[str] = Field(None, max_length=100)
    transform_params: Optional[Dict[str, Any]] = None


class FeatureResponse(BaseModel):
    id: UUID
    group_id: UUID
    name: str
    dtype: Optional[str]
    mean: Optional[float]
    std: Optional[float]
    min_val: Optional[float]
    max_val: Optional[float]
    null_rate: Optional[float]
    transform: Optional[str]
    transform_params: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class FeatureGroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    entity: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    features: List[FeatureResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
