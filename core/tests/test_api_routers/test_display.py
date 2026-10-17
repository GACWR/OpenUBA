'''
Copyright 2019-Present The OpenUBA Platform Authors
display api router tests
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


@pytest.mark.parametrize("path", [
    "/api/v1/display/home/summary",
    "/api/v1/display/get_all_users",
    "/api/v1/display/get_all_entities",
    "/api/v1/display/get_system_log",
])
def test_display_requires_authentication(unauthenticated_client: TestClient, path: str):
    '''display proxy must never be reachable unauthenticated (leaks users/entities/logs)'''
    assert unauthenticated_client.get(path).status_code == 401


def test_get_home_summary(test_client: TestClient):
    '''
    test getting home dashboard summary
    '''
    response = test_client.get("/api/v1/display/home/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_models" in data
    assert "active_models" in data
    assert "total_anomalies" in data
    assert "unacknowledged_anomalies" in data
    assert "open_cases" in data
    assert isinstance(data["total_models"], int)
    assert isinstance(data["total_anomalies"], int)

