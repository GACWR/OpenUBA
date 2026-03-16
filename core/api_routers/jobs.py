'''
Copyright 2019-Present The OpenUBA Platform Authors
jobs api router
'''

import asyncio
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from core.db import get_db
from core.repositories.job_repository import JobRepository
from core.api_schemas.jobs import (
    JobCreate, JobUpdate, JobResponse,
    JobLogCreate, JobLogResponse,
    TrainingMetricCreate, TrainingMetricResponse
)
from core.auth import require_permission, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "write"))
):
    '''
    create a new job
    '''
    repo = JobRepository(db)
    job = repo.create(
        name=job_data.name,
        model_id=job_data.model_id,
        job_type=job_data.job_type,
        created_by=UUID(current_user["user_id"]),
        dataset_id=job_data.dataset_id,
        hardware_tier=job_data.hardware_tier,
        hyperparameters=job_data.hyperparameters
    )
    logger.info(f"job created: {job.id}")
    return job


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None, pattern="^(pending|running|succeeded|failed|cancelled)$"),
    job_type: Optional[str] = Query(None),
    model_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "read"))
):
    '''
    list jobs with optional filters
    '''
    repo = JobRepository(db)
    jobs = repo.list_all(
        status=status,
        job_type=job_type,
        model_id=model_id,
        limit=limit,
        offset=offset
    )
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "read"))
):
    '''
    get job by id
    '''
    repo = JobRepository(db)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.patch("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "write"))
):
    '''
    update job fields
    '''
    repo = JobRepository(db)
    job = repo.update(job_id, **job_data.dict(exclude_unset=True))
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "write"))
):
    '''
    delete a job
    '''
    repo = JobRepository(db)
    success = repo.delete(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="job not found")


@router.get("/jobs/{job_id}/logs", response_model=List[JobLogResponse])
async def get_job_logs(
    job_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "read"))
):
    '''
    get logs for a job
    '''
    repo = JobRepository(db)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    logs = repo.get_logs(job_id, limit=limit)
    return logs


@router.get("/jobs/{job_id}/metrics", response_model=List[TrainingMetricResponse])
async def get_job_metrics(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "read"))
):
    '''
    get training metrics for a job
    '''
    repo = JobRepository(db)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    metrics = repo.get_metrics(job_id)
    return metrics


@router.post("/internal/metrics/{job_id}", response_model=TrainingMetricResponse, status_code=201)
async def post_training_metric(
    job_id: UUID,
    metric_data: TrainingMetricCreate,
    db: Session = Depends(get_db)
):
    '''
    post a training metric for a job (internal endpoint, no auth required)
    used by training containers to report metrics back to the platform
    '''
    repo = JobRepository(db)
    metric = repo.add_metric(
        job_id=job_id,
        metric_name=metric_data.metric_name,
        metric_value=metric_data.metric_value,
        epoch=metric_data.epoch,
        step=metric_data.step
    )
    if not metric:
        raise HTTPException(status_code=404, detail="job not found")
    logger.info(f"metric posted for job {job_id}: {metric_data.metric_name}={metric_data.metric_value}")
    return metric


@router.get("/jobs/{job_id}/metrics/stream")
async def stream_job_metrics(
    job_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("jobs", "read"))
):
    '''
    SSE endpoint for streaming job metrics in real-time
    the frontend connects to this and receives metric updates as they happen
    '''
    import json

    repo = JobRepository(db)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    async def event_generator():
        last_count = 0
        last_status = job.status
        while True:
            if await request.is_disconnected():
                break

            metrics = repo.get_metrics(job_id)
            current_count = len(metrics)

            if current_count > last_count:
                new_metrics = metrics[last_count:]
                for m in new_metrics:
                    yield {
                        "event": "metric",
                        "data": json.dumps({
                            "metric_name": m.metric_name,
                            "metric_value": m.metric_value,
                            "epoch": m.epoch,
                            "step": m.step,
                            "created_at": str(m.created_at),
                        })
                    }
                last_count = current_count

            # send job status updates only when something changed
            job_now = repo.get_by_id(job_id)
            if job_now:
                if job_now.status != last_status or current_count > last_count:
                    yield {
                        "event": "status",
                        "data": json.dumps({
                            "status": job_now.status,
                            "progress": job_now.progress,
                            "epoch_current": job_now.epoch_current,
                            "epoch_total": job_now.epoch_total,
                            "loss": job_now.loss,
                        })
                    }
                    last_status = job_now.status
                if job_now.status in ("succeeded", "failed", "cancelled"):
                    yield {"event": "done", "data": json.dumps({"status": job_now.status})}
                    break

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())


@router.post("/internal/logs/{job_id}", response_model=JobLogResponse, status_code=201)
async def post_job_log(
    job_id: UUID,
    log_data: JobLogCreate,
    db: Session = Depends(get_db)
):
    '''
    post a log entry for a job (internal endpoint, no auth required)
    used by training containers to send logs back to the platform
    '''
    repo = JobRepository(db)
    job_log = repo.add_log(
        job_id=job_id,
        message=log_data.message,
        level=log_data.level,
        logger_name=log_data.logger_name
    )
    if not job_log:
        raise HTTPException(status_code=404, detail="job not found")
    logger.info(f"log posted for job {job_id}")
    return job_log
