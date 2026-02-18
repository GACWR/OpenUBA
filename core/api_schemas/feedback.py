'''
Copyright 2019-Present The OpenUBA Platform Authors
pydantic schemas for user feedback
'''

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    anomaly_id: UUID
    feedback_type: str = Field(..., pattern="^(true_positive|false_positive|needs_review)$")
    notes: Optional[str] = None
    user_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: UUID
    anomaly_id: UUID
    feedback_type: str
    notes: Optional[str]
    user_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

