'''
Copyright 2019-Present The OpenUBA Platform Authors
pydantic schemas for anomalies
'''

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AnomalyCreate(BaseModel):
    model_id: UUID
    entity_id: str = Field(..., min_length=1)
    entity_type: str = Field(default="user", pattern="^(user|device|ip|other)$")
    risk_score: float = Field(..., ge=0.0, le=100.0)
    anomaly_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    model_config = {'protected_namespaces': ()}


class AnomalyResponse(BaseModel):
    id: UUID
    model_id: Optional[UUID]
    entity_id: Optional[str]
    entity_type: str
    timestamp: datetime
    risk_score: Optional[float]
    anomaly_type: Optional[str]
    details: Optional[Dict[str, Any]]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime

    @field_validator('risk_score', mode='before')
    @classmethod
    def convert_risk_score(cls, v):
        if v is None:
            return None
        from decimal import Decimal
        if isinstance(v, Decimal):
            return float(v)
        return v

    model_config = {
        'from_attributes': True,
        'protected_namespaces': ()
    }


class AnomalyListResponse(BaseModel):
    items: List[AnomalyResponse]
    total: int
    limit: int
    offset: int

