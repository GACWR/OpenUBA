'''
Copyright 2019-Present The OpenUBA Platform Authors
cases api router tests
'''

import pytest
from uuid import uuid4
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


def test_create_case(test_client: TestClient):
    '''
    test creating a case
    '''
    case_data = {
        "title": "test case",
        "description": "test case description",
        "severity": "high",
        "analyst_notes": "initial notes"
    }
    response = test_client.post("/api/v1/cases", json=case_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "test case"
    assert data["severity"] == "high"
    assert data["status"] == "open"
    assert "id" in data


def test_list_cases(test_client: TestClient):
    '''
    test listing cases
    '''
    # create a case first
    case_data = {
        "title": "list test case",
        "description": "test",
        "severity": "medium"
    }
    test_client.post("/api/v1/cases", json=case_data)
    
    # list cases
    response = test_client.get("/api/v1/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_case(test_client: TestClient):
    '''
    test getting a case by id
    '''
    # create a case
    case_data = {
        "title": "get test case",
        "description": "test",
        "severity": "low"
    }
    create_response = test_client.post("/api/v1/cases", json=case_data)
    case_id = create_response.json()["id"]
    
    # get the case
    response = test_client.get(f"/api/v1/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["title"] == "get test case"


def test_update_case(test_client: TestClient):
    '''
    test updating a case
    '''
    # create a case
    case_data = {
        "title": "update test case",
        "description": "test",
        "severity": "medium"
    }
    create_response = test_client.post("/api/v1/cases", json=case_data)
    case_id = create_response.json()["id"]
    
    # update the case
    update_data = {"status": "investigating", "analyst_notes": "updated notes"}
    response = test_client.patch(f"/api/v1/cases/{case_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "investigating"
    assert data["analyst_notes"] == "updated notes"


@pytest.mark.parametrize("path", ["/api/v1/cases", f"/api/v1/cases/{uuid4()}"])
def test_case_reads_require_authentication(unauthenticated_client: TestClient, path: str):
    '''GET case reads must reject unauthenticated callers (issue #147)'''
    assert unauthenticated_client.get(path).status_code == 401

