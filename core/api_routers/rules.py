'''
Copyright 2019-Present The OpenUBA Platform Authors
rules api router
'''

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.db import get_db
from core.db.models import Rule, Alert
from core.api_schemas.rules import RuleCreate, RuleUpdate, RuleResponse, AlertResponse
from core.auth import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("rules", "write"))
):
    '''
    create a new detection rule
    '''
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        rule_type=rule_data.rule_type,
        condition=rule_data.condition,
        features=rule_data.features,
        score=rule_data.score,
        enabled=rule_data.enabled,
        severity=rule_data.severity,
        flow_graph=rule_data.flow_graph
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info(f"created rule: {rule.id}")
    return rule


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    enabled: Optional[bool] = Query(None),
    rule_type: Optional[str] = Query(None, pattern="^(single-fire|deviation|flow)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    '''
    get or list detection rules
    '''
    query = db.query(Rule)
    if enabled is not None:
        query = query.filter(Rule.enabled == enabled)
    if rule_type:
        query = query.filter(Rule.rule_type == rule_type)
    rules = query.limit(limit).offset(offset).all()
    return rules


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    '''
    get rule by id
    '''
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule


@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("rules", "write"))
):
    '''
    update rule fields
    '''
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    update_data = rule_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    logger.info(f"updated rule: {rule_id}")
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("rules", "write"))
):
    '''
    delete a rule
    '''
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    db.delete(rule)
    db.commit()
    logger.info(f"deleted rule: {rule_id}")


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    severity: Optional[str] = Query(None, pattern="^(critical|high|medium|low)$"),
    acknowledged: Optional[bool] = Query(None),
    rule_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    '''
    list alerts with optional filters
    '''
    query = db.query(Alert).order_by(Alert.created_at.desc())
    if severity:
        query = query.filter(Alert.severity == severity)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    if rule_id:
        query = query.filter(Alert.rule_id == rule_id)
    alerts = query.limit(limit).offset(offset).all()
    return alerts
