'''
Copyright 2019-Present The OpenUBA Platform Authors
hyperparameter repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import HyperparameterSet


class HyperparameterRepository:
    '''
    repository for hyperparameter set database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        parameters: Dict[str, Any],
        created_by: UUID,
        model_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> HyperparameterSet:
        '''
        create a new hyperparameter set record
        '''
        hp_set = HyperparameterSet(
            name=name,
            parameters=parameters,
            created_by=created_by,
            model_id=model_id,
            description=description
        )
        self.db.add(hp_set)
        self.db.commit()
        self.db.refresh(hp_set)
        logging.info(f"created hyperparameter set: {hp_set.id}")
        return hp_set

    def get_by_id(self, hp_id: UUID) -> Optional[HyperparameterSet]:
        '''
        get hyperparameter set by id
        '''
        return self.db.query(HyperparameterSet).filter(HyperparameterSet.id == hp_id).first()

    def list_all(
        self,
        model_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[HyperparameterSet]:
        '''
        list all hyperparameter sets with optional filters
        '''
        query = self.db.query(HyperparameterSet)
        if model_id:
            query = query.filter(HyperparameterSet.model_id == model_id)
        if created_by:
            query = query.filter(HyperparameterSet.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, hp_id: UUID, **kwargs) -> Optional[HyperparameterSet]:
        '''
        update hyperparameter set fields
        '''
        hp_set = self.get_by_id(hp_id)
        if not hp_set:
            return None
        for key, value in kwargs.items():
            if hasattr(hp_set, key):
                setattr(hp_set, key, value)
        self.db.commit()
        self.db.refresh(hp_set)
        logging.info(f"updated hyperparameter set: {hp_id}")
        return hp_set

    def delete(self, hp_id: UUID) -> bool:
        '''
        delete a hyperparameter set
        '''
        hp_set = self.get_by_id(hp_id)
        if not hp_set:
            return False
        self.db.delete(hp_set)
        self.db.commit()
        logging.info(f"deleted hyperparameter set: {hp_id}")
        return True
