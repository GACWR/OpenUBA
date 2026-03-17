'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for jobs management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


@pytest.fixture
def test_model_for_jobs(backend_url: str, auth_headers: dict):
    '''
    create a test model for job tests
    '''
    model_name = f"e2e_test_model_{uuid4().hex[:8]}"
    model_data = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    response = requests.post(f"{backend_url}/api/v1/models", json=model_data, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


def test_jobs_page_loads(page: Page, frontend_url: str):
    '''
    test that jobs page loads
    '''
    page.goto(f"{frontend_url}/jobs")
    page.wait_for_load_state("networkidle")
    assert "Jobs" in page.title() or "jobs" in page.content().lower()


def test_create_job_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test creating a job via API and verifying in database
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {
        "name": job_name,
        "model_id": test_model_for_jobs["id"],
        "job_type": "training",
        "hardware_tier": "cpu-small"
    }

    response = requests.post(
        f"{backend_url}/api/v1/jobs",
        json=job_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create job failed: {response.text}"
    job = response.json()
    job_id = job["id"]

    # verify in database
    db_job = db_utils.query_generic("jobs", job_id)
    assert db_job is not None
    assert db_job["job_type"] == "training"
    assert db_job["status"] == "pending"


def test_list_jobs_via_api(
    backend_url: str,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test listing jobs via API
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {
        "name": job_name,
        "model_id": test_model_for_jobs["id"],
        "job_type": "training"
    }
    requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/jobs", headers=auth_headers)
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0


def test_get_job_by_id(
    backend_url: str,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test getting job by id
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "inference"}
    create_resp = requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["job_type"] == "inference"


def test_update_job_status(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test updating job status
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "training"}
    create_resp = requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_resp.json()["id"]

    update_resp = requests.patch(
        f"{backend_url}/api/v1/jobs/{job_id}",
        json={"status": "running"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "running"

    db_job = db_utils.query_generic("jobs", job_id)
    assert db_job["status"] == "running"


def test_delete_job_via_api(
    backend_url: str,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test deleting a job
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "training"}
    create_resp = requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/jobs/{job_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_post_job_metrics_internal(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test posting training metrics via internal endpoint (no auth)
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "training"}
    create_resp = requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_resp.json()["id"]

    # post metric (internal - no auth)
    metric_data = {
        "metric_name": "loss",
        "metric_value": 0.42,
        "epoch": 1,
        "step": 100
    }
    metric_resp = requests.post(f"{backend_url}/api/v1/internal/metrics/{job_id}", json=metric_data)
    assert metric_resp.status_code == 201

    # verify via authenticated endpoint
    metrics_resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}/metrics", headers=auth_headers)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert len(metrics) > 0
    assert metrics[0]["metric_name"] == "loss"


def test_post_job_logs_internal(
    backend_url: str,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test posting job logs via internal endpoint (no auth)
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "training"}
    create_resp = requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_resp.json()["id"]

    # post log (internal - no auth)
    log_data = {
        "message": "training epoch 1 started",
        "level": "INFO",
        "logger_name": "model_runner"
    }
    log_resp = requests.post(f"{backend_url}/api/v1/internal/logs/{job_id}", json=log_data)
    assert log_resp.status_code == 201

    # verify via authenticated endpoint
    logs_resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}/logs", headers=auth_headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) > 0
    assert "training epoch 1" in logs[0]["message"]


def test_job_not_found(
    backend_url: str,
    auth_headers: dict
):
    '''
    test 404 for non-existent job
    '''
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = requests.get(f"{backend_url}/api/v1/jobs/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_job_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict,
    test_model_for_jobs: dict
):
    '''
    test that job created via API appears in UI
    '''
    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_data = {"name": job_name, "model_id": test_model_for_jobs["id"], "job_type": "training"}
    requests.post(f"{backend_url}/api/v1/jobs", json=job_data, headers=auth_headers)

    page.goto(f"{frontend_url}/jobs")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={job_name}").is_visible()
