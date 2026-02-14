'''
Copyright 2019-Present The OpenUBA Platform Authors
pydantic schemas for cases
'''

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    analyst_notes: Optional[str] = None
    assigned_to: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|investigating|resolved|closed)$")
    severity: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    analyst_notes: Optional[str] = None
    assigned_to: Optional[str] = None


class CaseResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    severity: str
    analyst_notes: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True

