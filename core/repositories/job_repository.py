'''
Copyright 2019-Present The OpenUBA Platform Authors
job repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Job, JobLog, TrainingMetric


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
        hyperparameters: Optional[Dict[str, Any]] = None
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
            hyperparameters=hyperparameters
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
        return query.limit(limit).offset(offset).all()

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

    def get_logs(self, job_id: UUID, limit: int = 1000) -> List[JobLog]:
        '''
        get all logs for a job
        '''
        return self.db.query(JobLog).filter(
            JobLog.job_id == job_id
        ).order_by(JobLog.created_at).limit(limit).all()

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
