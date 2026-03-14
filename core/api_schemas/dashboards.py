'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[List[Any]] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[List[Any]] = None
    published: Optional[bool] = None


class DashboardResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    layout: Optional[List[Any]]
    published: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
