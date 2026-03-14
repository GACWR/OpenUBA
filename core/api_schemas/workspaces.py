'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    environment: str = Field(default="default", max_length=100)
    hardware_tier: str = Field(default="cpu-small", max_length=50)
    ide: str = Field(default="jupyterlab", max_length=50)
    timeout_hours: int = Field(default=24, ge=1)


class WorkspaceUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|starting|running|stopping|stopped|failed)$")
    hardware_tier: Optional[str] = Field(None, max_length=50)
    timeout_hours: Optional[int] = Field(None, ge=1)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    environment: str
    hardware_tier: str
    ide: str
    status: str
    pod_name: Optional[str]
    service_name: Optional[str]
    pvc_name: Optional[str]
    access_url: Optional[str]
    node_port: Optional[int]
    cr_name: Optional[str]
    created_by: Optional[UUID]
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    timeout_hours: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
