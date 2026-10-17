'''
Copyright 2019-Present The OpenUBA Platform Authors
source_groups api router tests — auth coverage (closes the unauthenticated
read/write gap; relates to issue #127)
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


def test_create_source_group(test_client: TestClient):
    '''admin can create a source group'''
    payload = {
        "slug": "test-group",
        "description": "test source group",
        "config": [{"type": "local_fs", "path": "/tmp/x"}],
    }
    response = test_client.post("/api/v1/source_groups/", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["slug"] == "test-group"
    assert "id" in data


def test_list_source_groups(test_client: TestClient):
    '''admin can list source groups'''
    test_client.post("/api/v1/source_groups/", json={
        "slug": "list-group", "config": [{"type": "local_fs"}],
    })
    response = test_client.get("/api/v1/source_groups/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.parametrize(
    "path", ["/api/v1/source_groups/", f"/api/v1/source_groups/{uuid4()}"]
)
def test_source_group_reads_require_authentication(unauthenticated_client: TestClient, path: str):
    '''GET source_group reads must reject unauthenticated callers (#127)'''
    assert unauthenticated_client.get(path).status_code == 401


def test_source_group_create_requires_authentication(unauthenticated_client: TestClient):
    '''POST create must reject unauthenticated callers — the real write gap (#127)'''
    resp = unauthenticated_client.post(
        "/api/v1/source_groups/",
        json={"slug": "unauth", "config": [{"type": "local_fs"}]},
    )
    assert resp.status_code == 401


def test_source_group_update_requires_authentication(unauthenticated_client: TestClient):
    '''PUT update must reject unauthenticated callers — the real write gap (#127)'''
    resp = unauthenticated_client.put(
        f"/api/v1/source_groups/{uuid4()}",
        json={"slug": "unauth", "config": [{"type": "local_fs"}]},
    )
    assert resp.status_code == 401
