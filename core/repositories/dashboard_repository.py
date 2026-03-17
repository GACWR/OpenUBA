'''
Copyright 2019-Present The OpenUBA Platform Authors
dashboard repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Dashboard


class DashboardRepository:
    '''
    repository for dashboard database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        layout: Optional[List[Dict[str, Any]]] = None
    ) -> Dashboard:
        '''
        create a new dashboard record
        '''
        dashboard = Dashboard(
            name=name,
            created_by=created_by,
            description=description,
            layout=layout
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        logging.info(f"created dashboard: {dashboard.id}")
        return dashboard

    def get_by_id(self, dashboard_id: UUID) -> Optional[Dashboard]:
        '''
        get dashboard by id
        '''
        return self.db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()

    def list_all(
        self,
        published: Optional[bool] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dashboard]:
        '''
        list all dashboards with optional filters
        '''
        query = self.db.query(Dashboard)
        if published is not None:
            query = query.filter(Dashboard.published == published)
        if created_by:
            query = query.filter(Dashboard.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, dashboard_id: UUID, **kwargs) -> Optional[Dashboard]:
        '''
        update dashboard fields
        '''
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return None
        for key, value in kwargs.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)
        self.db.commit()
        self.db.refresh(dashboard)
        logging.info(f"updated dashboard: {dashboard_id}")
        return dashboard

    def delete(self, dashboard_id: UUID) -> bool:
        '''
        delete a dashboard
        '''
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return False
        self.db.delete(dashboard)
        self.db.commit()
        logging.info(f"deleted dashboard: {dashboard_id}")
        return True
