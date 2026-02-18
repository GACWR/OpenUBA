'''
Copyright 2019-Present The OpenUBA Platform Authors
pydantic schemas for models
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ModelComponentResponse(BaseModel):
    id: UUID
    filename: str
    component_type: str
    file_hash: str
    data_hash: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    source_type: str = Field(..., pattern="^(openuba_hub|github|huggingface|kubeflow|local_fs)$")
    source_url: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    author: Optional[str] = None
    enabled: bool = True
    runtime: Optional[str] = Field("python-base", pattern="^(python-base|sklearn|pytorch|tensorflow|networkx)$")


class ModelUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|installed|active|disabled)$")
    enabled: Optional[bool] = None
    description: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None
    runtime: Optional[str] = Field(None, pattern="^(python-base|sklearn|pytorch|tensorflow|networkx)$")


class ModelResponse(BaseModel):
    id: UUID
    name: str
    version: str
    source_type: str
    source_url: Optional[str]
    manifest: Optional[Dict[str, Any]]
    status: str
    enabled: bool
    description: Optional[str]
    author: Optional[str]
    runtime: str
    created_at: datetime
    updated_at: datetime
    components: List[ModelComponentResponse] = []

    class Config:
        from_attributes = True

