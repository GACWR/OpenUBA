'''
Copyright 2019-Present The OpenUBA Platform Authors
anomalies api router tests
'''

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from core.fastapi_app import app
from core.auth import get_current_user
from core.db.connection import get_db


@pytest.fixture(autouse=True)
def _as_admin():
    '''authenticate every request in this module as an admin (bypasses require_permission)'''
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "admin", "user_id": str(uuid4()), "role": "admin", "payload": {},
    }
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def unauthenticated_client(_as_admin):
    '''client with NO auth override → protected routes must 401'''
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = lambda: object()
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)


def test_create_anomaly(test_client: TestClient):
    '''
    test creating an anomaly
    '''
    # first create a model
    model_data = {
        "name": "anomaly_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    # create anomaly
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user123",
        "entity_type": "user",
        "risk_score": 85.5,
        "anomaly_type": "behavioral",
        "details": {"test": "data"},
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/api/v1/anomalies", json=anomaly_data)
    assert response.status_code == 201
    data = response.json()
    assert data["entity_id"] == "user123"
    assert data["risk_score"] == 85.5
    assert "id" in data


def test_list_anomalies(test_client: TestClient):
    '''
    test listing anomalies
    '''
    # create a model and anomaly first
    model_data = {
        "name": "list_anomaly_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user456",
        "entity_type": "user",
        "risk_score": 75.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    test_client.post("/api/v1/anomalies", json=anomaly_data)
    
    # list anomalies
    response = test_client.get("/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_anomaly(test_client: TestClient):
    '''
    test getting an anomaly by id
    '''
    # create model and anomaly
    model_data = {
        "name": "get_anomaly_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user789",
        "entity_type": "user",
        "risk_score": 90.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    create_response = test_client.post("/api/v1/anomalies", json=anomaly_data)
    anomaly_id = create_response.json()["id"]
    
    # get the anomaly
    response = test_client.get(f"/api/v1/anomalies/{anomaly_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == anomaly_id
    assert data["entity_id"] == "user789"


def test_acknowledge_anomaly(test_client: TestClient):
    '''
    test acknowledging an anomaly
    '''
    # create model and anomaly
    model_data = {
        "name": "ack_anomaly_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user999",
        "entity_type": "user",
        "risk_score": 80.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    create_response = test_client.post("/api/v1/anomalies", json=anomaly_data)
    anomaly_id = create_response.json()["id"]
    
    # acknowledge the anomaly
    response = test_client.post(
        f"/api/v1/anomalies/{anomaly_id}/acknowledge",
        params={"acknowledged_by": "test_user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["acknowledged"] == True
    assert data["acknowledged_by"] == "test_user"


@pytest.mark.parametrize(
    "path", ["/api/v1/anomalies", f"/api/v1/anomalies/{uuid4()}"]
)
def test_anomaly_reads_require_authentication(unauthenticated_client: TestClient, path: str):
    '''GET anomaly reads must reject unauthenticated callers'''
    assert unauthenticated_client.get(path).status_code == 401

