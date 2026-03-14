'''
Copyright 2019-Present The OpenUBA Platform Authors
experiment repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Experiment, ExperimentRun


class ExperimentRepository:
    '''
    repository for experiment database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        created_by: UUID,
        description: Optional[str] = None
    ) -> Experiment:
        '''
        create a new experiment record
        '''
        experiment = Experiment(
            name=name,
            created_by=created_by,
            description=description
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        logging.info(f"created experiment: {experiment.id}")
        return experiment

    def get_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        '''
        get experiment by id
        '''
        return self.db.query(Experiment).filter(Experiment.id == experiment_id).first()

    def list_all(
        self,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Experiment]:
        '''
        list all experiments with optional filters
        '''
        query = self.db.query(Experiment)
        if created_by:
            query = query.filter(Experiment.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def delete(self, experiment_id: UUID) -> bool:
        '''
        delete an experiment
        '''
        experiment = self.get_by_id(experiment_id)
        if not experiment:
            return False
        self.db.delete(experiment)
        self.db.commit()
        logging.info(f"deleted experiment: {experiment_id}")
        return True

    def add_run(
        self,
        experiment_id: UUID,
        created_by: UUID,
        job_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        status: str = "pending"
    ) -> Optional[ExperimentRun]:
        '''
        add a run to an experiment
        '''
        experiment = self.get_by_id(experiment_id)
        if not experiment:
            return None
        run = ExperimentRun(
            experiment_id=experiment_id,
            created_by=created_by,
            job_id=job_id,
            model_id=model_id,
            parameters=parameters,
            metrics=metrics,
            status=status
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        logging.info(f"added run to experiment {experiment_id}")
        return run

    def get_runs(self, experiment_id: UUID) -> List[ExperimentRun]:
        '''
        get all runs for an experiment
        '''
        return self.db.query(ExperimentRun).filter(
            ExperimentRun.experiment_id == experiment_id
        ).all()

    def update_run(self, run_id: UUID, **kwargs) -> Optional[ExperimentRun]:
        '''
        update experiment run fields
        '''
        run = self.db.query(ExperimentRun).filter(ExperimentRun.id == run_id).first()
        if not run:
            return None
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        self.db.commit()
        self.db.refresh(run)
        logging.info(f"updated experiment run: {run_id}")
        return run
