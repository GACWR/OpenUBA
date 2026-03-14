'''
Copyright 2019-Present The OpenUBA Platform Authors
dataset repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import Dataset


class DatasetRepository:
    '''
    repository for dataset database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        source_type: str = "upload",
        format: str = "csv",
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
        columns: Optional[List[Dict[str, Any]]] = None
    ) -> Dataset:
        '''
        create a new dataset record
        '''
        dataset = Dataset(
            name=name,
            created_by=created_by,
            description=description,
            source_type=source_type,
            format=format,
            file_path=file_path,
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            columns=columns
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        logging.info(f"created dataset: {dataset.id}")
        return dataset

    def get_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        '''
        get dataset by id
        '''
        return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_by_name(self, name: str) -> Optional[Dataset]:
        '''
        get dataset by name
        '''
        return self.db.query(Dataset).filter(Dataset.name == name).first()

    def list_all(
        self,
        source_type: Optional[str] = None,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dataset]:
        '''
        list all datasets with optional filters
        '''
        query = self.db.query(Dataset)
        if source_type:
            query = query.filter(Dataset.source_type == source_type)
        if created_by:
            query = query.filter(Dataset.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def update(self, dataset_id: UUID, **kwargs) -> Optional[Dataset]:
        '''
        update dataset fields
        '''
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            return None
        for key, value in kwargs.items():
            if hasattr(dataset, key):
                setattr(dataset, key, value)
        self.db.commit()
        self.db.refresh(dataset)
        logging.info(f"updated dataset: {dataset_id}")
        return dataset

    def delete(self, dataset_id: UUID) -> bool:
        '''
        delete a dataset
        '''
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            return False
        self.db.delete(dataset)
        self.db.commit()
        logging.info(f"deleted dataset: {dataset_id}")
        return True
