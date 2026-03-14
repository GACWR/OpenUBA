'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class VisualizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    backend: str = Field(..., min_length=1, max_length=50)
    output_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    refresh_interval: int = Field(default=0, ge=0)


class VisualizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    rendered_output: Optional[str] = None
    refresh_interval: Optional[int] = Field(None, ge=0)
    published: Optional[bool] = None


class VisualizationResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    backend: str
    output_type: str
    code: Optional[str]
    data: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    rendered_output: Optional[str]
    refresh_interval: int
    published: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
