'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for workspaces api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_launch_workspace(test_client: TestClient):
    '''
    test launching a workspace
    '''
    response = test_client.post("/api/v1/workspaces/launch", json={
        "name": "test-workspace",
        "hardware_tier": "cpu-small",
        "environment": "default",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-workspace"
    assert data["status"] == "pending"
    assert data["hardware_tier"] == "cpu-small"
    assert data["environment"] == "default"
    assert data["ide"] == "jupyterlab"
    assert "id" in data


def test_launch_workspace_defaults(test_client: TestClient):
    '''
    test launching a workspace with default values
    '''
    response = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-defaults-test",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ws-defaults-test"
    assert data["environment"] == "default"
    assert data["hardware_tier"] == "cpu-small"
    assert data["ide"] == "jupyterlab"
    assert data["timeout_hours"] == 24


def test_list_workspaces(test_client: TestClient):
    '''
    test listing workspaces
    '''
    # create one first
    test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-list-test",
        "hardware_tier": "cpu-small",
    })
    response = test_client.get("/api/v1/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_workspace(test_client: TestClient):
    '''
    test getting workspace by id
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-get-test",
    })
    ws_id = create.json()["id"]
    response = test_client.get(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ws_id
    assert response.json()["name"] == "ws-get-test"


def test_get_workspace_not_found(test_client: TestClient):
    '''
    test 404 for nonexistent workspace
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/workspaces/{fake_id}")
    assert response.status_code == 404


def test_stop_workspace(test_client: TestClient):
    '''
    test stopping a workspace
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-stop-test",
    })
    ws_id = create.json()["id"]
    response = test_client.post(f"/api/v1/workspaces/{ws_id}/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


def test_stop_workspace_already_stopped(test_client: TestClient):
    '''
    test stopping an already stopped workspace returns 400
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-stop-twice-test",
    })
    ws_id = create.json()["id"]
    test_client.post(f"/api/v1/workspaces/{ws_id}/stop")
    response = test_client.post(f"/api/v1/workspaces/{ws_id}/stop")
    assert response.status_code == 400


def test_restart_workspace(test_client: TestClient):
    '''
    test restarting a stopped workspace
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-restart-test",
    })
    ws_id = create.json()["id"]
    # stop first
    test_client.post(f"/api/v1/workspaces/{ws_id}/stop")
    # restart
    response = test_client.post(f"/api/v1/workspaces/{ws_id}/restart")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_restart_workspace_not_stopped(test_client: TestClient):
    '''
    test restarting a workspace that is not stopped returns 400
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-restart-bad-test",
    })
    ws_id = create.json()["id"]
    response = test_client.post(f"/api/v1/workspaces/{ws_id}/restart")
    assert response.status_code == 400


def test_delete_workspace(test_client: TestClient):
    '''
    test deleting a workspace
    '''
    create = test_client.post("/api/v1/workspaces/launch", json={
        "name": "ws-delete-test",
    })
    ws_id = create.json()["id"]
    response = test_client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/workspaces/{ws_id}")
    assert get_resp.status_code == 404


def test_delete_workspace_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent workspace returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/workspaces/{fake_id}")
    assert response.status_code == 404
