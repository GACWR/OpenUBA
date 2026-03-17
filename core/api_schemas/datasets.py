'''
Copyright 2019-Present The OpenUBA Platform Authors
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: str = Field(default="upload", max_length=50)
    format: str = Field(default="csv", max_length=50)


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    source_type: str
    file_path: Optional[str]
    file_size: Optional[int]
    row_count: Optional[int]
    column_count: Optional[int]
    columns: Optional[List[Any]]
    format: str
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
