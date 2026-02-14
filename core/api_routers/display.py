'''
Copyright 2019-Present The OpenUBA Platform Authors
display api router - migrated from flask
'''

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.db import get_db
from core.db.models import Anomaly, Model, Case
from core.api import API, APIType

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/display/{display_type}")
async def get_display(
    display_type: str,
    db: Session = Depends(get_db)
):
    '''
    endpoint to get varied display information
    migrated from flask /display/<display_type>/
    supports: get_all_entities, get_all_users, get_home_summary, get_system_log
    '''
    try:
        # use existing api logic for compatibility
        result = API.get_display_of_type(display_type)
        return result
    except Exception as e:
        logger.error(f"display error: {e}")
        raise HTTPException(status_code=500, detail=f"display error: {str(e)}")


@router.get("/display/home/summary")
async def get_home_summary(
    db: Session = Depends(get_db)
):
    '''
    get home dashboard summary statistics
    '''
    # get counts from database
    total_models = db.query(func.count(Model.id)).scalar() or 0
    active_models = db.query(func.count(Model.id)).filter(
        Model.enabled == True,
        Model.status == "active"
    ).scalar() or 0
    total_anomalies = db.query(func.count(Anomaly.id)).scalar() or 0
    unacknowledged_anomalies = db.query(func.count(Anomaly.id)).filter(
        Anomaly.acknowledged == False
    ).scalar() or 0
    open_cases = db.query(func.count(Case.id)).filter(
        Case.status == "open"
    ).scalar() or 0
    
    return {
        "total_models": total_models,
        "active_models": active_models,
        "total_anomalies": total_anomalies,
        "unacknowledged_anomalies": unacknowledged_anomalies,
        "open_cases": open_cases
    }

