'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for pipelines management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_pipelines_page_loads(page: Page, frontend_url: str):
    '''
    test that pipelines page loads
    '''
    page.goto(f"{frontend_url}/pipelines")
    page.wait_for_load_state("networkidle")
    assert "Pipelines" in page.title() or "pipelines" in page.content().lower()


def test_create_pipeline_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating pipeline via API
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {
        "name": pipe_name,
        "description": "test pipeline",
        "steps": [
            {"type": "training", "config": {"epochs": 10}},
            {"type": "inference", "config": {"batch_size": 32}}
        ]
    }

    response = requests.post(
        f"{backend_url}/api/v1/pipelines",
        json=pipe_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create pipeline failed: {response.text}"
    pipeline = response.json()
    pipe_id = pipeline["id"]

    db_pipe = db_utils.query_generic("pipelines", pipe_id)
    assert db_pipe is not None
    assert db_pipe["name"] == pipe_name


def test_list_pipelines_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing pipelines via API
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/pipelines", headers=auth_headers)
    assert response.status_code == 200
    pipelines = response.json()
    assert isinstance(pipelines, list)
    assert len(pipelines) > 0


def test_get_pipeline_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting pipeline by id
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    create_resp = requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)
    pipe_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/pipelines/{pipe_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == pipe_name


def test_update_pipeline_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test updating pipeline
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "description": "original", "steps": [{"type": "training"}]}
    create_resp = requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)
    pipe_id = create_resp.json()["id"]

    update_resp = requests.put(
        f"{backend_url}/api/v1/pipelines/{pipe_id}",
        json={"description": "updated pipeline"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated pipeline"


def test_run_pipeline(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test triggering a pipeline run
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    create_resp = requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)
    pipe_id = create_resp.json()["id"]

    run_resp = requests.post(
        f"{backend_url}/api/v1/pipelines/{pipe_id}/run",
        headers=auth_headers
    )
    assert run_resp.status_code == 201, f"Run pipeline failed: {run_resp.text}"
    run = run_resp.json()
    assert run["status"] == "pending"

    db_run = db_utils.query_generic("pipeline_runs", run["id"])
    assert db_run is not None


def test_list_pipeline_runs(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing runs for a pipeline
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    create_resp = requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)
    pipe_id = create_resp.json()["id"]

    # create two runs
    requests.post(f"{backend_url}/api/v1/pipelines/{pipe_id}/run", headers=auth_headers)
    requests.post(f"{backend_url}/api/v1/pipelines/{pipe_id}/run", headers=auth_headers)

    runs_resp = requests.get(f"{backend_url}/api/v1/pipelines/{pipe_id}/runs", headers=auth_headers)
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) == 2


def test_delete_pipeline_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a pipeline
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    create_resp = requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)
    pipe_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/pipelines/{pipe_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/pipelines/{pipe_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_pipeline_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that pipeline created via API appears in UI
    '''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    pipe_data = {"name": pipe_name, "steps": [{"type": "training"}]}
    requests.post(f"{backend_url}/api/v1/pipelines", json=pipe_data, headers=auth_headers)

    page.goto(f"{frontend_url}/pipelines")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={pipe_name}").is_visible()
