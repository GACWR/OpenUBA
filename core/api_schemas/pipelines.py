'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[Any] = Field(...)


class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[Any]] = None


class PipelineResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    steps: List[Any]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineRunCreate(BaseModel):
    pipeline_id: UUID


class PipelineRunResponse(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: str
    current_step: int
    step_statuses: Optional[List[Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True
