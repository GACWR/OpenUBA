'''
Copyright 2019-Present The OpenUBA Platform Authors
feature repository for database operations
'''

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from core.db.models import FeatureGroup, Feature


class FeatureRepository:
    '''
    repository for feature store database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create_group(
        self,
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        entity: str = "default"
    ) -> FeatureGroup:
        '''
        create a new feature group
        '''
        group = FeatureGroup(
            name=name,
            created_by=created_by,
            description=description,
            entity=entity
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        logging.info(f"created feature group: {group.id}")
        return group

    def get_group_by_id(self, group_id: UUID) -> Optional[FeatureGroup]:
        '''
        get feature group by id
        '''
        return self.db.query(FeatureGroup).filter(FeatureGroup.id == group_id).first()

    def get_group_by_name(self, name: str) -> Optional[FeatureGroup]:
        '''
        get feature group by name
        '''
        return self.db.query(FeatureGroup).filter(FeatureGroup.name == name).first()

    def list_groups(
        self,
        created_by: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeatureGroup]:
        '''
        list all feature groups with optional filters
        '''
        query = self.db.query(FeatureGroup)
        if created_by:
            query = query.filter(FeatureGroup.created_by == created_by)
        return query.limit(limit).offset(offset).all()

    def delete_group(self, group_id: UUID) -> bool:
        '''
        delete a feature group
        '''
        group = self.get_group_by_id(group_id)
        if not group:
            return False
        self.db.delete(group)
        self.db.commit()
        logging.info(f"deleted feature group: {group_id}")
        return True

    def add_feature(
        self,
        group_id: UUID,
        name: str,
        dtype: Optional[str] = None,
        mean: Optional[float] = None,
        std: Optional[float] = None,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        null_rate: Optional[float] = None,
        transform: Optional[str] = None,
        transform_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Feature]:
        '''
        add a feature to a feature group
        '''
        group = self.get_group_by_id(group_id)
        if not group:
            return None
        feature = Feature(
            group_id=group_id,
            name=name,
            dtype=dtype,
            mean=mean,
            std=std,
            min_val=min_val,
            max_val=max_val,
            null_rate=null_rate,
            transform=transform,
            transform_params=transform_params
        )
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        logging.info(f"added feature {name} to group {group_id}")
        return feature

    def get_features(self, group_id: UUID) -> List[Feature]:
        '''
        get all features for a feature group
        '''
        return self.db.query(Feature).filter(
            Feature.group_id == group_id
        ).all()
