'''
Copyright 2019-Present The OpenUBA Platform Authors
anomaly repository for database operations
'''

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from core.db.models import Anomaly


class AnomalyRepository:
    '''
    repository for anomaly database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        model_id: UUID,
        entity_id: str,
        risk_score: Optional[float] = None,
        anomaly_type: Optional[str] = None,
        entity_type: str = "user",
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        run_id: Optional[UUID] = None
    ) -> Anomaly:
        '''
        create a new anomaly record
        '''
        from decimal import Decimal

        anomaly = Anomaly(
            model_id=model_id,
            run_id=run_id,
            entity_id=entity_id,
            entity_type=entity_type,
            risk_score=Decimal(str(risk_score)) if risk_score is not None else None,
            anomaly_type=anomaly_type,
            details=details,
            timestamp=timestamp or datetime.now(timezone.utc)
        )
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        logging.info(f"created anomaly: {anomaly.id}")
        return anomaly

    def get_by_id(self, anomaly_id: UUID) -> Optional[Anomaly]:
        '''
        get anomaly by id
        '''
        return self.db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()

    def list_all(
        self,
        model_id: Optional[UUID] = None,
        entity_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Anomaly]:
        '''
        list all anomalies with optional filters
        '''
        query = self.db.query(Anomaly)
        if model_id:
            query = query.filter(Anomaly.model_id == model_id)
        if entity_id:
            query = query.filter(Anomaly.entity_id == entity_id)
        if acknowledged is not None:
            query = query.filter(Anomaly.acknowledged == acknowledged)
        if min_risk_score is not None:
            query = query.filter(Anomaly.risk_score >= min_risk_score)
        if max_risk_score is not None:
            query = query.filter(Anomaly.risk_score <= max_risk_score)
        if start_time:
            query = query.filter(Anomaly.timestamp >= start_time)
        if end_time:
            query = query.filter(Anomaly.timestamp <= end_time)
        return query.order_by(desc(Anomaly.timestamp)).limit(limit).offset(offset).all()

    def acknowledge(
        self,
        anomaly_id: UUID,
        acknowledged_by: str
    ) -> Optional[Anomaly]:
        '''
        acknowledge an anomaly
        '''
        anomaly = self.get_by_id(anomaly_id)
        if not anomaly:
            return None
        from datetime import datetime
        anomaly.acknowledged = True
        anomaly.acknowledged_at = datetime.now(timezone.utc)
        anomaly.acknowledged_by = acknowledged_by
        self.db.commit()
        self.db.refresh(anomaly)
        logging.info(f"acknowledged anomaly: {anomaly_id}")
        return anomaly

    def delete(self, anomaly_id: UUID) -> bool:
        '''
        delete an anomaly
        '''
        anomaly = self.get_by_id(anomaly_id)
        if not anomaly:
            return False
        self.db.delete(anomaly)
        self.db.commit()
        logging.info(f"deleted anomaly: {anomaly_id}")
        return True

