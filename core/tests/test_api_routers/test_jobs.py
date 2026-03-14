'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for jobs api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_model(test_client: TestClient) -> str:
    '''helper to create a model and return its id'''
    model_data = {
        "name": f"job-test-model-{uuid4().hex[:8]}",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True,
    }
    response = test_client.post("/api/v1/models", json=model_data)
    return response.json()["id"]


def _create_job(test_client: TestClient, model_id: str = None) -> dict:
    '''helper to create a job and return the response data'''
    if model_id is None:
        model_id = _create_model(test_client)
    job_data = {
        "model_id": model_id,
        "job_type": "training",
        "hardware_tier": "cpu-small",
        "hyperparameters": {"learning_rate": 0.01, "epochs": 10},
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    return response.json()


def test_create_job(test_client: TestClient):
    '''
    test creating a job
    '''
    model_id = _create_model(test_client)
    job_data = {
        "model_id": model_id,
        "job_type": "training",
        "hardware_tier": "cpu-small",
        "hyperparameters": {"learning_rate": 0.01},
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    assert response.status_code == 201
    data = response.json()
    assert data["job_type"] == "training"
    assert data["status"] == "pending"
    assert data["hardware_tier"] == "cpu-small"
    assert data["hyperparameters"]["learning_rate"] == 0.01
    assert "id" in data


def test_list_jobs(test_client: TestClient):
    '''
    test listing jobs
    '''
    _create_job(test_client)
    response = test_client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_job(test_client: TestClient):
    '''
    test getting a job by id
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["job_type"] == "training"


def test_get_job_not_found(test_client: TestClient):
    '''
    test getting a nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


def test_update_job(test_client: TestClient):
    '''
    test updating a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    update_data = {
        "status": "running",
        "progress": 50,
    }
    response = test_client.patch(f"/api/v1/jobs/{job_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["progress"] == 50


def test_update_job_not_found(test_client: TestClient):
    '''
    test updating a nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.patch(f"/api/v1/jobs/{fake_id}", json={"status": "running"})
    assert response.status_code == 404


def test_delete_job(test_client: TestClient):
    '''
    test deleting a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 404


def test_delete_job_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


def test_get_job_logs(test_client: TestClient):
    '''
    test getting logs for a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_job_logs_not_found(test_client: TestClient):
    '''
    test getting logs for a nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}/logs")
    assert response.status_code == 404


def test_get_job_metrics(test_client: TestClient):
    '''
    test getting metrics for a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_job_metrics_not_found(test_client: TestClient):
    '''
    test getting metrics for a nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}/metrics")
    assert response.status_code == 404


def test_internal_post_metric(test_client: TestClient):
    '''
    test posting a training metric via internal endpoint (no auth)
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    metric_data = {
        "job_id": job_id,
        "metric_name": "loss",
        "metric_value": 0.5,
        "epoch": 1,
        "step": 100,
    }
    response = test_client.post(f"/api/v1/internal/metrics/{job_id}", json=metric_data)
    assert response.status_code == 201
    data = response.json()
    assert data["metric_name"] == "loss"
    assert data["metric_value"] == 0.5
    assert data["epoch"] == 1
    assert data["step"] == 100
    assert data["job_id"] == job_id


def test_internal_post_metric_multiple(test_client: TestClient):
    '''
    test posting multiple metrics for a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    # post multiple metrics
    for epoch in range(1, 4):
        metric_data = {
            "job_id": job_id,
            "metric_name": "loss",
            "metric_value": 1.0 / epoch,
            "epoch": epoch,
        }
        response = test_client.post(f"/api/v1/internal/metrics/{job_id}", json=metric_data)
        assert response.status_code == 201

    # verify metrics can be retrieved
    response = test_client.get(f"/api/v1/jobs/{job_id}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) >= 3


def test_internal_post_log(test_client: TestClient):
    '''
    test posting a log entry via internal endpoint (no auth)
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    log_data = {
        "job_id": job_id,
        "message": "training started",
        "level": "info",
        "logger_name": "trainer",
    }
    response = test_client.post(f"/api/v1/internal/logs/{job_id}", json=log_data)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "training started"
    assert data["level"] == "info"
    assert data["logger_name"] == "trainer"
    assert data["job_id"] == job_id


def test_internal_post_log_multiple(test_client: TestClient):
    '''
    test posting multiple logs for a job
    '''
    job = _create_job(test_client)
    job_id = job["id"]
    # post multiple logs
    for i in range(5):
        log_data = {
            "job_id": job_id,
            "message": f"training step {i}",
            "level": "info",
        }
        response = test_client.post(f"/api/v1/internal/logs/{job_id}", json=log_data)
        assert response.status_code == 201

    # verify logs can be retrieved
    response = test_client.get(f"/api/v1/jobs/{job_id}/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 5


def test_internal_post_metric_job_not_found(test_client: TestClient):
    '''
    test posting metric for nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    metric_data = {
        "job_id": fake_id,
        "metric_name": "loss",
        "metric_value": 0.5,
    }
    response = test_client.post(f"/api/v1/internal/metrics/{fake_id}", json=metric_data)
    assert response.status_code == 404


def test_internal_post_log_job_not_found(test_client: TestClient):
    '''
    test posting log for nonexistent job returns 404
    '''
    fake_id = str(uuid4())
    log_data = {
        "job_id": fake_id,
        "message": "should fail",
        "level": "info",
    }
    response = test_client.post(f"/api/v1/internal/logs/{fake_id}", json=log_data)
    assert response.status_code == 404
