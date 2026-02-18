'''
Copyright 2019-Present The OpenUBA Platform Authors
case repository for database operations
'''

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.db.models import Case, CaseAnomaly


class CaseRepository:
    '''
    repository for case database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "open",
        severity: str = "medium",
        analyst_notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> Case:
        '''
        create a new case
        '''
        case = Case(
            title=title,
            description=description,
            status=status,
            severity=severity,
            analyst_notes=analyst_notes,
            assigned_to=assigned_to
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        logging.info(f"created case: {case.id}")
        return case

    def get_by_id(self, case_id: UUID) -> Optional[Case]:
        '''
        get case by id
        '''
        return self.db.query(Case).filter(Case.id == case_id).first()

    def list_all(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Case]:
        '''
        list all cases with optional filters
        '''
        query = self.db.query(Case)
        if status:
            query = query.filter(Case.status == status)
        if severity:
            query = query.filter(Case.severity == severity)
        if assigned_to:
            query = query.filter(Case.assigned_to == assigned_to)
        return query.order_by(desc(Case.created_at)).limit(limit).offset(offset).all()

    def update(
        self,
        case_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        analyst_notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> Optional[Case]:
        '''
        update case fields
        '''
        case = self.get_by_id(case_id)
        if not case:
            return None
        if title:
            case.title = title
        if description is not None:
            case.description = description
        if status:
            case.status = status
            if status in ["resolved", "closed"]:
                case.resolved_at = datetime.utcnow()
        if severity:
            case.severity = severity
        if analyst_notes is not None:
            case.analyst_notes = analyst_notes
        if assigned_to is not None:
            case.assigned_to = assigned_to
        self.db.commit()
        self.db.refresh(case)
        logging.info(f"updated case: {case_id}")
        return case

    def add_anomaly(self, case_id: UUID, anomaly_id: UUID) -> bool:
        '''
        link an anomaly to a case
        '''
        case = self.get_by_id(case_id)
        if not case:
            return False
        link = CaseAnomaly(case_id=case_id, anomaly_id=anomaly_id)
        self.db.add(link)
        self.db.commit()
        logging.info(f"linked anomaly {anomaly_id} to case {case_id}")
        return True

    def remove_anomaly(self, case_id: UUID, anomaly_id: UUID) -> bool:
        '''
        unlink an anomaly from a case
        '''
        link = self.db.query(CaseAnomaly).filter(
            CaseAnomaly.case_id == case_id,
            CaseAnomaly.anomaly_id == anomaly_id
        ).first()
        if not link:
            return False
        self.db.delete(link)
        self.db.commit()
        logging.info(f"unlinked anomaly {anomaly_id} from case {case_id}")
        return True

    def delete(self, case_id: UUID) -> bool:
        '''
        delete a case
        '''
        case = self.get_by_id(case_id)
        if not case:
            return False
        self.db.delete(case)
        self.db.commit()
        logging.info(f"deleted case: {case_id}")
        return True

