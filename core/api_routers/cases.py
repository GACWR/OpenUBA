'''
Copyright 2019-Present The OpenUBA Platform Authors
cases api router
'''

import logging
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.case_repository import CaseRepository
from core.api_schemas.cases import CaseCreate, CaseUpdate, CaseResponse
from core.auth import require_permission
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/cases", response_model=CaseResponse, status_code=201)
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("cases", "write"))
):
    '''
    create a new case
    '''
    repo = CaseRepository(db)
    case = repo.create(
        title=case_data.title,
        description=case_data.description,
        severity=case_data.severity,
        analyst_notes=case_data.analyst_notes,
        assigned_to=case_data.assigned_to
    )
    return case


@router.get("/cases", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[str] = Query(None, pattern="^(open|investigating|resolved|closed)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    '''
    list or search cases
    '''
    repo = CaseRepository(db)
    cases = repo.list_all(
        status=status,
        severity=severity,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset
    )
    return cases


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: Session = Depends(get_db)
):
    '''
    get case by id
    '''
    repo = CaseRepository(db)
    case = repo.get_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.patch("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("cases", "write"))
):
    '''
    update case fields
    '''
    repo = CaseRepository(db)
    case = repo.update(case_id, **case_data.dict(exclude_unset=True))
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.post("/cases/{case_id}/anomalies/{anomaly_id}")
async def link_anomaly_to_case(
    case_id: UUID,
    anomaly_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("cases", "write"))
):
    '''
    link an anomaly to a case
    '''
    repo = CaseRepository(db)
    success = repo.add_anomaly(case_id, anomaly_id)
    if not success:
        raise HTTPException(status_code=404, detail="case not found")
    return {"message": "anomaly linked to case"}


@router.delete("/cases/{case_id}/anomalies/{anomaly_id}")
async def unlink_anomaly_from_case(
    case_id: UUID,
    anomaly_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("cases", "write"))
):
    '''
    unlink an anomaly from a case
    '''
    repo = CaseRepository(db)
    success = repo.remove_anomaly(case_id, anomaly_id)
    if not success:
        raise HTTPException(status_code=404, detail="case or link not found")
    return {"message": "anomaly unlinked from case"}


@router.delete("/cases/{case_id}", status_code=204)
async def delete_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("cases", "write"))
):
    '''
    delete a case
    '''
    repo = CaseRepository(db)
    success = repo.delete(case_id)
    if not success:
        raise HTTPException(status_code=404, detail="case not found")

