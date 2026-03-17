'''
Copyright 2019-Present The OpenUBA Platform Authors
job repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Job, JobLog, TrainingMetric, ModelRun, ModelLog


# map ModelRun status to Job status
_RUN_STATUS_MAP = {
    "pending": "pending",
    "dispatched": "pending",
    "running": "running",
    "succeeded": "succeeded",
    "failed": "failed",
}


class JobRepository:
    '''
    repository for job database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        model_id: UUID,
        job_type: str,
        created_by: UUID,
        name: Optional[str] = None,
        dataset_id: Optional[UUID] = None,
        hardware_tier: str = "cpu-small",
        hyperparameters: Optional[Dict[str, Any]] = None,
        model_run_id: Optional[UUID] = None,
    ) -> Job:
        '''
        create a new job record
        '''
        job = Job(
            name=name,
            model_id=model_id,
            job_type=job_type,
            created_by=created_by,
            dataset_id=dataset_id,
            hardware_tier=hardware_tier,
            hyperparameters=hyperparameters,
            model_run_id=model_run_id,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logging.info(f"created job: {job.id}")
        return job

    def get_by_id(self, job_id: UUID) -> Optional[Job]:
        '''
        get job by id
        '''
        return self.db.query(Job).filter(Job.id == job_id).first()

    def sync_from_model_run(self, job: Job) -> Job:
        '''
        sync job status/timestamps from linked ModelRun
        called at read time so the Job reflects the actual execution state
        '''
        if not job.model_run_id:
            return job
        run = self.db.query(ModelRun).filter(ModelRun.id == job.model_run_id).first()
        if not run:
            return job

        mapped_status = _RUN_STATUS_MAP.get(run.status, run.status)
        changed = False
        if job.status != mapped_status:
            job.status = mapped_status
            changed = True
        if run.started_at and job.started_at != run.started_at:
            job.started_at = run.started_at
            changed = True
        if run.finished_at and job.completed_at != run.finished_at:
            job.completed_at = run.finished_at
            changed = True
        if run.error_message and job.error_message != run.error_message:
            job.error_message = run.error_message
            changed = True
        if run.result_summary and not job.metrics:
            job.metrics = run.result_summary
            changed = True

        if changed:
            self.db.commit()
            self.db.refresh(job)
        return job

    def list_all(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        model_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        '''
        list all jobs with optional filters
        '''
        query = self.db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        if job_type:
            query = query.filter(Job.job_type == job_type)
        if model_id:
            query = query.filter(Job.model_id == model_id)
        if created_by:
            query = query.filter(Job.created_by == created_by)
        jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()
        # sync status from linked model runs
        for job in jobs:
            self.sync_from_model_run(job)
        return jobs

    def update(self, job_id: UUID, **kwargs) -> Optional[Job]:
        '''
        update job fields
        '''
        job = self.get_by_id(job_id)
        if not job:
            return None
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        logging.info(f"updated job: {job_id}")
        return job

    def delete(self, job_id: UUID) -> bool:
        '''
        delete a job
        '''
        job = self.get_by_id(job_id)
        if not job:
            return False
        self.db.delete(job)
        self.db.commit()
        logging.info(f"deleted job: {job_id}")
        return True

    def add_log(
        self,
        job_id: UUID,
        message: str,
        level: str = "info",
        logger_name: Optional[str] = None
    ) -> Optional[JobLog]:
        '''
        add a log entry to a job
        '''
        job = self.get_by_id(job_id)
        if not job:
            return None
        job_log = JobLog(
            job_id=job_id,
            message=message,
            level=level,
            logger_name=logger_name
        )
        self.db.add(job_log)
        self.db.commit()
        self.db.refresh(job_log)
        logging.info(f"added log to job {job_id}")
        return job_log

    def get_logs(self, job_id: UUID, limit: int = 1000) -> List:
        '''
        get all logs for a job
        falls back to model_logs if no job_logs exist and a model_run is linked
        '''
        logs = self.db.query(JobLog).filter(
            JobLog.job_id == job_id
        ).order_by(JobLog.created_at).limit(limit).all()

        if logs:
            return logs

        # fall back to model_logs from linked ModelRun
        job = self.get_by_id(job_id)
        if job and job.model_run_id:
            model_logs = self.db.query(ModelLog).filter(
                ModelLog.model_run_id == job.model_run_id
            ).order_by(ModelLog.created_at).limit(limit).all()
            return model_logs

        return []

    def add_metric(
        self,
        job_id: UUID,
        metric_name: str,
        metric_value: float,
        epoch: Optional[int] = None,
        step: Optional[int] = None
    ) -> Optional[TrainingMetric]:
        '''
        add a training metric to a job
        '''
        job = self.get_by_id(job_id)
        if not job:
            return None
        metric = TrainingMetric(
            job_id=job_id,
            metric_name=metric_name,
            metric_value=metric_value,
            epoch=epoch,
            step=step
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        logging.info(f"added metric {metric_name} to job {job_id}")
        return metric

    def get_metrics(self, job_id: UUID) -> List[TrainingMetric]:
        '''
        get all training metrics for a job
        '''
        return self.db.query(TrainingMetric).filter(
            TrainingMetric.job_id == job_id
        ).order_by(TrainingMetric.created_at).all()
