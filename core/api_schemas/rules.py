'''
Copyright 2019-Present The OpenUBA Platform Authors
pydantic schemas for rules
'''

from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import json


class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., pattern="^(single-fire|deviation|flow)$")
    condition: str = Field(default="flow-based rule", min_length=1)
    features: Optional[Union[str, List[str]]] = None
    score: int = Field(default=0, ge=0)
    enabled: bool = True
    severity: Optional[str] = Field(default="medium", pattern="^(critical|high|medium|low)$")
    flow_graph: Optional[dict] = None

    @field_validator('features', mode='before')
    @classmethod
    def convert_features(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return json.dumps(v)
        return v


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, pattern="^(single-fire|deviation|flow)$")
    condition: Optional[str] = Field(None, min_length=1)
    features: Optional[str] = None
    score: Optional[int] = Field(None, ge=0)
    enabled: Optional[bool] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    flow_graph: Optional[dict] = None


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    rule_type: str
    condition: str
    features: Optional[str]
    score: int
    enabled: bool
    severity: Optional[str]
    flow_graph: Optional[dict]
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: UUID
    rule_id: UUID
    severity: str
    message: str
    entity_id: Optional[str]
    entity_type: Optional[str]
    alert_context: Optional[dict]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
