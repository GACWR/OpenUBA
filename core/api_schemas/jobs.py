'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    model_id: UUID
    dataset_id: Optional[UUID] = None
    job_type: str = Field(..., min_length=1, max_length=50)
    hardware_tier: str = Field(default="cpu-small", max_length=50)
    hyperparameters: Optional[Dict[str, Any]] = None

    model_config = {'protected_namespaces': ()}


class JobUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|running|succeeded|failed|cancelled)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class JobResponse(BaseModel):
    id: UUID
    name: Optional[str]
    model_id: Optional[UUID]
    dataset_id: Optional[UUID]
    job_type: str
    status: str
    cr_name: Optional[str]
    k8s_job_name: Optional[str]
    hardware_tier: str
    hyperparameters: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    progress: int
    epoch_current: Optional[int]
    epoch_total: Optional[int]
    loss: Optional[float]
    learning_rate: Optional[float]
    error_message: Optional[str]
    created_by: UUID
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {
        'from_attributes': True,
        'protected_namespaces': ()
    }


class JobLogCreate(BaseModel):
    job_id: Optional[UUID] = None
    level: str = Field(default="info", max_length=20)
    message: str = Field(..., min_length=1)
    logger_name: Optional[str] = None


class JobLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    level: str
    message: str
    logger_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingMetricCreate(BaseModel):
    job_id: Optional[UUID] = None
    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_value: float
    epoch: Optional[int] = None
    step: Optional[int] = None


class TrainingMetricResponse(BaseModel):
    id: UUID
    job_id: UUID
    metric_name: str
    metric_value: float
    epoch: Optional[int]
    step: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
