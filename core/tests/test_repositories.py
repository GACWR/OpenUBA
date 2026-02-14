'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for repositories
'''

import pytest
from uuid import uuid4
from core.repositories.model_repository import ModelRepository
from core.repositories.anomaly_repository import AnomalyRepository
from core.repositories.case_repository import CaseRepository

# use db_session from conftest which uses testcontainers


def test_model_repository_create(db_session):
    '''
    test creating a model
    '''
    repo = ModelRepository(db_session)
    model = repo.create(
        name="test_model",
        version="1.0.0",
        source_type="local_fs",
        description="test model"
    )
    assert model.id is not None
    assert model.name == "test_model"
    assert model.version == "1.0.0"


def test_model_repository_get_by_id(db_session):
    '''
    test getting a model by id
    '''
    repo = ModelRepository(db_session)
    model = repo.create(
        name="test_model",
        version="1.0.0",
        source_type="local_fs"
    )
    retrieved = repo.get_by_id(model.id)
    assert retrieved is not None
    assert retrieved.id == model.id


def test_anomaly_repository_create(db_session):
    '''
    test creating an anomaly
    '''
    # create a model first
    model_repo = ModelRepository(db_session)
    model = model_repo.create(
        name="test_model",
        version="1.0.0",
        source_type="local_fs"
    )
    
    # create anomaly
    anomaly_repo = AnomalyRepository(db_session)
    anomaly = anomaly_repo.create(
        model_id=model.id,
        entity_id="user123",
        risk_score=75.5
    )
    assert anomaly.id is not None
    assert anomaly.entity_id == "user123"
    assert anomaly.risk_score == 75.5


def test_case_repository_create(db_session):
    '''
    test creating a case
    '''
    repo = CaseRepository(db_session)
    case = repo.create(
        title="test case",
        description="test description",
        severity="high"
    )
    assert case.id is not None
    assert case.title == "test case"
    assert case.severity == "high"

