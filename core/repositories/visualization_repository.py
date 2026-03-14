'''
Copyright 2019-Present The OpenUBA Platform Authors
visualization repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Visualization


class VisualizationRepository:
    '''
    repository for visualization database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        backend: str,
        output_type: str,
        created_by: UUID,
        description: Optional[str] = None,
        code: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        refresh_interval: int = 0
    ) -> Visualization:
        '''
        create a new visualization record
        '''
        visualization = Visualization(
            name=name,
            backend=backend,
            output_type=output_type,
            created_by=created_by,
            description=description,
            code=code,
            data=data,
            config=config,
            refresh_interval=refresh_interval
        )
        self.db.add(visualization)
        self.db.commit()
        self.db.refresh(visualization)
        logging.info(f"created visualization: {visualization.id}")
        return visualization

    def get_by_id(self, viz_id: UUID) -> Optional[Visualization]:
        '''
        get visualization by id
        '''
        return self.db.query(Visualization).filter(Visualization.id == viz_id).first()

    def list_all(
        self,
        published: Optional[bool] = None,
        backend: Optional[str] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Visualization]:
        '''
        list all visualizations with optional filters
        '''
        query = self.db.query(Visualization)
        if published is not None:
            query = query.filter(Visualization.published == published)
        if backend:
            query = query.filter(Visualization.backend == backend)
        if created_by:
            query = query.filter(Visualization.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, viz_id: UUID, **kwargs) -> Optional[Visualization]:
        '''
        update visualization fields
        '''
        visualization = self.get_by_id(viz_id)
        if not visualization:
            return None
        for key, value in kwargs.items():
            if hasattr(visualization, key):
                setattr(visualization, key, value)
        self.db.commit()
        self.db.refresh(visualization)
        logging.info(f"updated visualization: {viz_id}")
        return visualization

    def delete(self, viz_id: UUID) -> bool:
        '''
        delete a visualization
        '''
        visualization = self.get_by_id(viz_id)
        if not visualization:
            return False
        self.db.delete(visualization)
        self.db.commit()
        logging.info(f"deleted visualization: {viz_id}")
        return True
