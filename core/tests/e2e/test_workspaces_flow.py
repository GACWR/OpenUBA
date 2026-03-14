'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for workspace management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_workspaces_page_loads(page: Page, frontend_url: str):
    '''
    test that workspaces page loads
    '''
    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")
    assert "Workspaces" in page.title() or "workspaces" in page.content().lower()


def test_create_workspace_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating workspace via API and verifying in database
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {
        "name": ws_name,
        "environment": "default",
        "hardware_tier": "cpu-small",
        "ide": "jupyterlab",
        "timeout_hours": 1
    }

    response = requests.post(
        f"{backend_url}/api/v1/workspaces/launch",
        json=ws_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create workspace failed: {response.text}"
    workspace = response.json()
    ws_id = workspace["id"]

    # verify in database
    db_ws = db_utils.query_generic("workspaces", ws_id)
    assert db_ws is not None
    assert db_ws["name"] == ws_name
    assert db_ws["hardware_tier"] == "cpu-small"
    assert db_ws["status"] == "pending"


def test_list_workspaces_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing workspaces via API
    '''
    # create a workspace
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {
        "name": ws_name,
        "environment": "default",
        "hardware_tier": "cpu-small",
        "ide": "jupyterlab"
    }
    requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)

    # list workspaces
    response = requests.get(f"{backend_url}/api/v1/workspaces", headers=auth_headers)
    assert response.status_code == 200
    workspaces = response.json()
    assert isinstance(workspaces, list)
    assert len(workspaces) > 0


def test_get_workspace_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting workspace by id
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"}
    create_resp = requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)
    assert create_resp.status_code == 201
    ws_id = create_resp.json()["id"]

    # get by id
    resp = requests.get(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == ws_name


def test_stop_workspace_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test stopping a workspace
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"}
    create_resp = requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)
    ws_id = create_resp.json()["id"]

    # stop workspace
    stop_resp = requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"

    # verify in database
    db_ws = db_utils.query_generic("workspaces", ws_id)
    assert db_ws["status"] == "stopped"


def test_restart_workspace_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test restarting a stopped workspace
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"}
    create_resp = requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)
    ws_id = create_resp.json()["id"]

    # stop first
    requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)

    # restart
    restart_resp = requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/restart", headers=auth_headers)
    assert restart_resp.status_code == 200
    assert restart_resp.json()["status"] == "pending"


def test_delete_workspace_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a workspace
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"}
    create_resp = requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)
    ws_id = create_resp.json()["id"]

    # delete
    del_resp = requests.delete(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # verify deleted
    get_resp = requests.get(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_workspace_not_found(
    backend_url: str,
    auth_headers: dict
):
    '''
    test 404 for non-existent workspace
    '''
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = requests.get(f"{backend_url}/api/v1/workspaces/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_workspace_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that workspace created via API appears in UI
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"}
    requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)

    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={ws_name}").is_visible()


def test_workspace_lifecycle_full(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test full workspace lifecycle: create -> stop -> restart -> delete
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    ws_data = {"name": ws_name, "environment": "default", "hardware_tier": "cpu-large", "ide": "jupyterlab", "timeout_hours": 2}

    # create
    resp = requests.post(f"{backend_url}/api/v1/workspaces/launch", json=ws_data, headers=auth_headers)
    assert resp.status_code == 201
    ws_id = resp.json()["id"]
    assert resp.json()["hardware_tier"] == "cpu-large"

    # stop
    resp = requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"

    # restart
    resp = requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/restart", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # delete
    resp = requests.delete(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert resp.status_code == 204

    # verify gone
    db_ws = db_utils.query_generic("workspaces", ws_id)
    assert db_ws is None
