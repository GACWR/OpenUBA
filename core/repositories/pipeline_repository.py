'''
Copyright 2019-Present The OpenUBA Platform Authors
pipeline repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Pipeline, PipelineRun


class PipelineRepository:
    '''
    repository for pipeline database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        created_by: UUID,
        description: Optional[str] = None
    ) -> Pipeline:
        '''
        create a new pipeline record
        '''
        pipeline = Pipeline(
            name=name,
            steps=steps,
            created_by=created_by,
            description=description
        )
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        logging.info(f"created pipeline: {pipeline.id}")
        return pipeline

    def get_by_id(self, pipeline_id: UUID) -> Optional[Pipeline]:
        '''
        get pipeline by id
        '''
        return self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    def list_all(
        self,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Pipeline]:
        '''
        list all pipelines with optional filters
        '''
        query = self.db.query(Pipeline)
        if created_by:
            query = query.filter(Pipeline.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, pipeline_id: UUID, **kwargs) -> Optional[Pipeline]:
        '''
        update pipeline fields
        '''
        pipeline = self.get_by_id(pipeline_id)
        if not pipeline:
            return None
        for key, value in kwargs.items():
            if hasattr(pipeline, key):
                setattr(pipeline, key, value)
        self.db.commit()
        self.db.refresh(pipeline)
        logging.info(f"updated pipeline: {pipeline_id}")
        return pipeline

    def delete(self, pipeline_id: UUID) -> bool:
        '''
        delete a pipeline
        '''
        pipeline = self.get_by_id(pipeline_id)
        if not pipeline:
            return False
        self.db.delete(pipeline)
        self.db.commit()
        logging.info(f"deleted pipeline: {pipeline_id}")
        return True

    def create_run(
        self,
        pipeline_id: UUID,
        created_by: UUID
    ) -> Optional[PipelineRun]:
        '''
        create a new run for a pipeline
        '''
        pipeline = self.get_by_id(pipeline_id)
        if not pipeline:
            return None
        run = PipelineRun(
            pipeline_id=pipeline_id,
            created_by=created_by
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        logging.info(f"created run for pipeline {pipeline_id}")
        return run

    def get_run(self, run_id: UUID) -> Optional[PipelineRun]:
        '''
        get pipeline run by id
        '''
        return self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()

    def list_runs(self, pipeline_id: UUID) -> List[PipelineRun]:
        '''
        get all runs for a pipeline
        '''
        return self.db.query(PipelineRun).filter(
            PipelineRun.pipeline_id == pipeline_id
        ).all()

    def update_run(self, run_id: UUID, **kwargs) -> Optional[PipelineRun]:
        '''
        update pipeline run fields
        '''
        run = self.get_run(run_id)
        if not run:
            return None
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        self.db.commit()
        self.db.refresh(run)
        logging.info(f"updated pipeline run: {run_id}")
        return run
