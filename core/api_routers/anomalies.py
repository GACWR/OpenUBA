'''
Copyright 2019-Present The OpenUBA Platform Authors
anomalies api router
'''

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.anomaly_repository import AnomalyRepository
from core.api_schemas.anomalies import AnomalyCreate, AnomalyResponse, AnomalyListResponse
from core.auth import require_permission
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/anomalies", response_model=AnomalyResponse, status_code=201)
async def create_anomaly(
    anomaly_data: AnomalyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("anomalies", "write"))
):
    '''
    create a new anomaly record
    '''
    repo = AnomalyRepository(db)
    anomaly = repo.create(
        model_id=anomaly_data.model_id,
        entity_id=anomaly_data.entity_id,
        entity_type=anomaly_data.entity_type,
        risk_score=anomaly_data.risk_score,
        anomaly_type=anomaly_data.anomaly_type,
        details=anomaly_data.details,
        timestamp=anomaly_data.timestamp
    )
    return anomaly


@router.get("/anomalies", response_model=AnomalyListResponse)
async def list_anomalies(
    model_id: Optional[UUID] = Query(None),
    entity_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    '''
    list anomalies with pagination and filters
    '''
    repo = AnomalyRepository(db)
    anomalies = repo.list_all(
        model_id=model_id,
        entity_id=entity_id,
        acknowledged=acknowledged,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    # get total count (simplified - in production would use a separate count query)
    total = len(anomalies)  # placeholder
    return AnomalyListResponse(
        items=anomalies,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: UUID,
    db: Session = Depends(get_db)
):
    '''
    get anomaly by id
    '''
    repo = AnomalyRepository(db)
    anomaly = repo.get_by_id(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="anomaly not found")
    return anomaly


@router.post("/anomalies/{anomaly_id}/acknowledge", response_model=AnomalyResponse)
async def acknowledge_anomaly(
    anomaly_id: UUID,
    acknowledged_by: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("anomalies", "write"))
):
    '''
    acknowledge an anomaly
    '''
    repo = AnomalyRepository(db)
    anomaly = repo.acknowledge(anomaly_id, acknowledged_by)
    if not anomaly:
        raise HTTPException(status_code=404, detail="anomaly not found")
    return anomaly


@router.delete("/anomalies/{anomaly_id}", status_code=204)
async def delete_anomaly(
    anomaly_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("anomalies", "write"))
):
    '''
    delete an anomaly
    '''
    repo = AnomalyRepository(db)
    success = repo.delete(anomaly_id)
    if not success:
        raise HTTPException(status_code=404, detail="anomaly not found")

