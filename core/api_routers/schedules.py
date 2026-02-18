'''
Copyright 2019-Present The OpenUBA Platform Authors
model schedule management router
'''

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.model_repository import ModelRepository
from core.services.model_scheduler import ModelScheduler
from core.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter()

# scheduler instance - will be initialized on first use
_scheduler_instance = None

def get_scheduler() -> ModelScheduler:
    '''
    get or create scheduler instance
    singleton pattern to ensure only one scheduler is running
    '''
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ModelScheduler()
    return _scheduler_instance


class ScheduleCreate(BaseModel):
    '''
    schedule creation model
    '''
    cron_expression: str  # format: "minute hour day month day_of_week"
    enabled: bool = True


class ScheduleResponse(BaseModel):
    '''
    schedule response model
    '''
    id: str
    model_id: str
    cron_expression: str
    enabled: bool
    next_run: Optional[str] = None


@router.post("/models/{model_id}/schedule", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    model_id: UUID,
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("schedules", "write"))
):
    '''
    create a schedule for model execution
    cron_expression format: "minute hour day month day_of_week"
    example: "0 2 * * *" (daily at 2 AM)
    '''
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    
    if model.status != "installed" and model.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"model must be installed or active to schedule, current status: {model.status}"
        )
    
    try:
        schedule_id = get_scheduler().create_schedule(
            model_id=model_id,
            cron_expression=schedule_data.cron_expression,
            enabled=schedule_data.enabled
        )
        
        # update model manifest with schedule info
        manifest = model.manifest or {}
        manifest["schedule"] = {
            "id": schedule_id,
            "cron_expression": schedule_data.cron_expression,
            "enabled": schedule_data.enabled
        }
        repo.update(model_id, manifest=manifest)
        
        logger.info(f"created schedule {schedule_id} for model {model_id}")
        
        return ScheduleResponse(
            id=schedule_id,
            model_id=str(model_id),
            cron_expression=schedule_data.cron_expression,
            enabled=schedule_data.enabled
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="failed to create schedule")


@router.delete("/models/{model_id}/schedule", status_code=204)
async def delete_schedule(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("schedules", "write"))
):
    '''
    delete schedule for a model
    '''
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    
    manifest = model.manifest or {}
    schedule_info = manifest.get("schedule")
    if not schedule_info:
        raise HTTPException(status_code=404, detail="no schedule found for model")
    
    schedule_id = schedule_info.get("id")
    if not schedule_id:
        raise HTTPException(status_code=404, detail="schedule id not found")
    
    try:
        get_scheduler().delete_schedule(schedule_id)
        
        # remove schedule from manifest
        manifest.pop("schedule", None)
        repo.update(model_id, manifest=manifest)
        
        logger.info(f"deleted schedule {schedule_id} for model {model_id}")
    except Exception as e:
        logger.error(f"failed to delete schedule: {e}")
        raise HTTPException(status_code=500, detail="failed to delete schedule")


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    current_user: dict = Depends(require_permission("schedules", "write")),
    db: Session = Depends(get_db)
):
    '''
    list all active schedules
    '''
    try:
        schedules = get_scheduler().list_schedules()
        
        # enrich with model info
        result = []
        repo = ModelRepository(db)
        for schedule in schedules:
            schedule_id = schedule["id"]
            # extract model_id from schedule_id (format: "model_{uuid}" or "model-schedule-{uuid}")
            if schedule_id.startswith("model_"):
                model_id_str = schedule_id.replace("model_", "")
            elif schedule_id.startswith("model-schedule-"):
                model_id_str = schedule_id.replace("model-schedule-", "")
            else:
                continue
            
            try:
                model_id = UUID(model_id_str)
                model = repo.get_by_id(model_id)
                if model:
                    manifest = model.manifest or {}
                    schedule_info = manifest.get("schedule", {})
                    result.append(ScheduleResponse(
                        id=schedule_id,
                        model_id=str(model_id),
                        cron_expression=schedule_info.get("cron_expression", ""),
                        enabled=schedule.get("suspended", False) if "suspended" in schedule else schedule_info.get("enabled", True),
                        next_run=schedule.get("next_run")
                    ))
            except ValueError:
                continue
        
        return result
    except Exception as e:
        logger.error(f"failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail="failed to list schedules")

