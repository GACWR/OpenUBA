'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for experiments management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_experiments_page_loads(page: Page, frontend_url: str):
    '''
    test that experiments page loads
    '''
    page.goto(f"{frontend_url}/experiments")
    page.wait_for_load_state("networkidle")
    assert "Experiments" in page.title() or "experiments" in page.content().lower()


def test_create_experiment_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating experiment via API and verifying in database
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {
        "name": exp_name,
        "description": "test experiment for e2e"
    }

    response = requests.post(
        f"{backend_url}/api/v1/experiments",
        json=exp_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create experiment failed: {response.text}"
    experiment = response.json()
    exp_id = experiment["id"]

    db_exp = db_utils.query_generic("experiments", exp_id)
    assert db_exp is not None
    assert db_exp["name"] == exp_name


def test_list_experiments_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing experiments via API
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "test"}
    requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/experiments", headers=auth_headers)
    assert response.status_code == 200
    experiments = response.json()
    assert isinstance(experiments, list)
    assert len(experiments) > 0


def test_get_experiment_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting experiment by id
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "test"}
    create_resp = requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)
    exp_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == exp_name


def test_add_experiment_run(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test adding a run to an experiment
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "test"}
    create_resp = requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)
    exp_id = create_resp.json()["id"]

    run_data = {
        "parameters": {"learning_rate": 0.001, "batch_size": 32},
        "metrics": {"accuracy": 0.95, "loss": 0.05}
    }
    run_resp = requests.post(
        f"{backend_url}/api/v1/experiments/{exp_id}/runs",
        json=run_data,
        headers=auth_headers
    )
    assert run_resp.status_code == 201, f"Add run failed: {run_resp.text}"
    run = run_resp.json()
    assert run["parameters"]["learning_rate"] == 0.001

    db_run = db_utils.query_generic("experiment_runs", run["id"])
    assert db_run is not None


def test_list_experiment_runs(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing runs for an experiment
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "test"}
    create_resp = requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)
    exp_id = create_resp.json()["id"]

    # add two runs
    for lr in [0.001, 0.01]:
        run_data = {"parameters": {"learning_rate": lr}, "metrics": {"accuracy": 0.9}}
        requests.post(f"{backend_url}/api/v1/experiments/{exp_id}/runs", json=run_data, headers=auth_headers)

    runs_resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}/runs", headers=auth_headers)
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) == 2


def test_compare_experiment_runs(
    backend_url: str,
    auth_headers: dict
):
    '''
    test comparing experiment runs
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "comparison test"}
    create_resp = requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)
    exp_id = create_resp.json()["id"]

    # add runs with different params
    for lr, acc in [(0.001, 0.95), (0.01, 0.90), (0.1, 0.85)]:
        run_data = {"parameters": {"learning_rate": lr}, "metrics": {"accuracy": acc}}
        requests.post(f"{backend_url}/api/v1/experiments/{exp_id}/runs", json=run_data, headers=auth_headers)

    compare_resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}/compare", headers=auth_headers)
    assert compare_resp.status_code == 200
    runs = compare_resp.json()
    assert len(runs) == 3


def test_delete_experiment_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting an experiment
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "to delete"}
    create_resp = requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)
    exp_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/experiments/{exp_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_experiment_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that experiment created via API appears in UI
    '''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    exp_data = {"name": exp_name, "description": "ui test"}
    requests.post(f"{backend_url}/api/v1/experiments", json=exp_data, headers=auth_headers)

    page.goto(f"{frontend_url}/experiments")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={exp_name}").is_visible()
