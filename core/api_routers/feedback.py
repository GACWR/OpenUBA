'''
Copyright 2019-Present The OpenUBA Platform Authors
user feedback api router
'''

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.db.models import UserFeedback
from core.api_schemas.feedback import FeedbackCreate, FeedbackResponse
from core.auth import get_current_user
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    '''
    submit feedback on an anomaly
    '''
    # verify anomaly exists
    from core.repositories.anomaly_repository import AnomalyRepository
    anomaly_repo = AnomalyRepository(db)
    anomaly = anomaly_repo.get_by_id(feedback_data.anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="anomaly not found")
    feedback = UserFeedback(
        anomaly_id=feedback_data.anomaly_id,
        feedback_type=feedback_data.feedback_type,
        notes=feedback_data.notes,
        user_id=feedback_data.user_id
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    logger.info(f"created feedback: {feedback.id}")
    return feedback


@router.get("/feedback", response_model=List[FeedbackResponse])
async def list_feedback(
    anomaly_id: UUID,
    db: Session = Depends(get_db)
):
    '''
    get feedback for an anomaly
    '''
    feedback_list = db.query(UserFeedback).filter(
        UserFeedback.anomaly_id == anomaly_id
    ).all()
    return feedback_list

