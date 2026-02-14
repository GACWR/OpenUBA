'''
Copyright 2019-Present The OpenUBA Platform Authors
model repository for database operations
'''

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.db.models import Model, ModelVersion, ModelComponent


class ModelRepository:
    '''
    repository for model database operations
    '''

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        version: str,
        source_type: str,
        slug: str,
        source_url: Optional[str] = None,
        manifest: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        enabled: bool = True,
        description: Optional[str] = None,
        author: Optional[str] = None,
        runtime: str = "python-base"
    ) -> Model:
        '''
        create a new model record
        '''
        model = Model(
            name=name,
            version=version,
            source_type=source_type,
            slug=slug,
            source_url=source_url,
            manifest=manifest,
            status=status,
            enabled=enabled,
            description=description,
            author=author,
            runtime=runtime
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        logging.info(f"created model: {model.id}")
        return model

    def get_by_id(self, model_id: UUID) -> Optional[Model]:
        '''
        get model by id
        '''
        return self.db.query(Model).filter(Model.id == model_id).first()

    def get_by_name_version(self, name: str, version: str) -> Optional[Model]:
        '''
        get model by name and version
        '''
        return self.db.query(Model).filter(
            and_(Model.name == name, Model.version == version)
        ).first()

    def list_all(
        self,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Model]:
        '''
        list all models with optional filters
        '''
        query = self.db.query(Model)
        if status:
            query = query.filter(Model.status == status)
        if source_type:
            query = query.filter(Model.source_type == source_type)
        if enabled is not None:
            query = query.filter(Model.enabled == enabled)
        return query.limit(limit).offset(offset).all()

    def update(self, model_id: UUID, **kwargs) -> Optional[Model]:
        '''
        update model fields
        '''
        model = self.get_by_id(model_id)
        if not model:
            return None
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        logging.info(f"updated model: {model_id}")
        return model

    def delete(self, model_id: UUID) -> bool:
        '''
        delete a model
        '''
        model = self.get_by_id(model_id)
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        logging.info(f"deleted model: {model_id}")
        return True

    def add_component(
        self,
        model_id: UUID,
        filename: str,
        component_type: str,
        file_hash: str,
        data_hash: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> Optional[ModelComponent]:
        '''
        add a component to a model
        '''
        model = self.get_by_id(model_id)
        if not model:
            return None
        component = ModelComponent(
            model_id=model_id,
            filename=filename,
            component_type=component_type,
            file_hash=file_hash,
            data_hash=data_hash,
            file_path=file_path,
            file_size=file_size
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        logging.info(f"added component {filename} to model {model_id}")
        return component

    def get_components(self, model_id: UUID) -> List[ModelComponent]:
        '''
        get all components for a model
        '''
        return self.db.query(ModelComponent).filter(
            ModelComponent.model_id == model_id
        ).all()

    def add_version(
        self,
        model_id: UUID,
        version: str,
        manifest: Optional[Dict[str, Any]] = None
    ) -> Optional[ModelVersion]:
        '''
        add a version record for a model
        '''
        model = self.get_by_id(model_id)
        if not model:
            return None
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            manifest=manifest
        )
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        logging.info(f"added version {version} to model {model_id}")
        return model_version

