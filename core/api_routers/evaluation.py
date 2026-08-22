'''
Copyright 2019-Present The OpenUBA Platform Authors
evaluation api router — score a model run's anomalies against known ground truth.

Reads a run's anomalies (by run_id) and scores them with the shared
core.services.detection_eval scorer. The result shape is JSONB-friendly so
callers can store it in an ExperimentRun.metrics for comparison (issue #35).
'''

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.anomaly_repository import AnomalyRepository
from core.services.detection_eval import evaluate_detections
from core.auth import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)


class EvaluateRunRequest(BaseModel):
    run_id: UUID
    malicious_entities: List[str] = Field(..., description="ground-truth malicious entity ids")
    all_entities: Optional[List[str]] = Field(None, description="full population for TN / FP-rate")
    threshold: float = Field(50.0, ge=0.0, le=100.0, description="risk_score to count as flagged")
    scenarios: Optional[Dict[str, List[str]]] = Field(None, description="scenario -> entity ids for per-scenario recall")


@router.post("/evaluate/run")
async def evaluate_run(
    body: EvaluateRunRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("anomalies", "read")),
):
    '''
    score one model run's detections against a labeled ground-truth entity set.
    returns precision / recall / F1 / false-positive-rate (+ per-scenario recall).
    '''
    repo = AnomalyRepository(db)
    rows = repo.list_all(run_id=body.run_id, limit=100000)
    anomalies = [
        {
            "entity_id": r.entity_id,
            "risk_score": float(r.risk_score) if r.risk_score is not None else 0.0,
            "anomaly_type": r.anomaly_type,
        }
        for r in rows
    ]
    result = evaluate_detections(
        anomalies=anomalies,
        malicious_entities=body.malicious_entities,
        all_entities=body.all_entities,
        threshold=body.threshold,
        scenarios=body.scenarios,
    )
    logger.info(
        f"evaluated run {body.run_id}: precision={result.precision} "
        f"recall={result.recall} over {len(anomalies)} anomalies"
    )
    return result.to_dict()
