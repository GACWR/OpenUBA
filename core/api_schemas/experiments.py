'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ExperimentRunCreate(BaseModel):
    experiment_id: Optional[UUID] = None
    job_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    parameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

    model_config = {'protected_namespaces': ()}


class ExperimentRunResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    job_id: Optional[UUID]
    model_id: Optional[UUID]
    parameters: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    status: str
    created_by: UUID
    created_at: datetime

    model_config = {
        'from_attributes': True,
        'protected_namespaces': ()
    }


class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    runs: List[ExperimentRunResponse] = []

    class Config:
        from_attributes = True


class HyperparameterSetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    model_id: Optional[UUID] = None
    parameters: Dict[str, Any] = Field(...)
    description: Optional[str] = None

    model_config = {'protected_namespaces': ()}


class HyperparameterSetResponse(BaseModel):
    id: UUID
    name: str
    model_id: Optional[UUID]
    parameters: Dict[str, Any]
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        'from_attributes': True,
        'protected_namespaces': ()
    }
