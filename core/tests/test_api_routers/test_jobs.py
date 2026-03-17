'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for jobs api router
'''

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.db.models import User

# stable user id so we can seed the DB
_ADMIN_USER_ID = str(uuid4())

MOCK_ADMIN_USER = {
    "user_id": _ADMIN_USER_ID,
    "username": "testadmin",
    "role": "admin",
}


@pytest.fixture(autouse=True)
def seed_admin_user(db_session: Session):
    '''seed the mock admin user in the database so FK constraints are satisfied'''
    existing = db_session.query(User).filter(User.id == UUID(_ADMIN_USER_ID)).first()
    if not existing:
        user = User(
            id=UUID(_ADMIN_USER_ID),
            username="testadmin",
            password_hash="not-a-real-hash",
            role="admin",
        )
        db_session.add(user)
        db_session.flush()
    yield


@pytest.fixture(autouse=True)
def override_auth():
    '''override auth for all tests in this module'''
    from core.fastapi_app import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def mock_orchestrator():
    '''mock ModelOrchestrator so create_job doesnt actually run Docker/K8s'''
    mock_run_id = uuid4()
    with patch('core.services.model_orchestrator.ModelOrchestrator') as mock_cls:
        mock_instance = MagicMock()
        mock_instance.execute_model_background.return_value = mock_run_id
        mock_cls.return_value = mock_instance
        yield mock_instance, mock_run_id


def _create_installed_model(test_client: TestClient) -> str:
    '''helper to create a model with status=installed and return its id'''
    model_data = {
        "name": f"job-test-model-{uuid4().hex[:8]}",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True,
    }
    response = test_client.post("/api/v1/models", json=model_data)
    model_id = response.json()["id"]
    # set status to installed so jobs can be created against it
    test_client.patch(f"/api/v1/models/{model_id}", json={"status": "installed"})
    return model_id


def _create_job(test_client: TestClient, model_id: str = None) -> dict:
    '''helper to create a job and return the response data'''
    if model_id is None:
        model_id = _create_installed_model(test_client)
    job_data = {
        "model_id": model_id,
        "job_type": "training",
        "hardware_tier": "cpu-small",
        "hyperparameters": {"learning_rate": 0.01, "epochs": 10},
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    return response.json()


def test_create_job(test_client: TestClient, mock_orchestrator):
    '''test creating a job triggers orchestrator and returns running status'''
    mock_instance, mock_run_id = mock_orchestrator
    model_id = _create_installed_model(test_client)
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
    assert data["status"] == "running"
    assert data["hardware_tier"] == "cpu-small"
    assert data["hyperparameters"]["learning_rate"] == 0.01
    assert data["model_run_id"] == str(mock_run_id)
    assert "id" in data


def test_create_job_calls_orchestrator(test_client: TestClient, mock_orchestrator):
    '''test that create_job actually calls the orchestrator'''
    mock_instance, _ = mock_orchestrator
    model_id = _create_installed_model(test_client)
    job_data = {
        "model_id": model_id,
        "job_type": "training",
        "hardware_tier": "cpu-small",
    }
    test_client.post("/api/v1/jobs", json=job_data)
    mock_instance.execute_model_background.assert_called_once()
    call_args = mock_instance.execute_model_background.call_args
    assert call_args[0][0] == UUID(model_id)
    assert call_args[1]["run_type"] == "train"


def test_create_inference_job(test_client: TestClient, mock_orchestrator):
    '''test creating an inference job maps to run_type=infer'''
    mock_instance, _ = mock_orchestrator
    model_id = _create_installed_model(test_client)
    job_data = {
        "model_id": model_id,
        "job_type": "inference",
        "hardware_tier": "cpu-small",
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    assert response.status_code == 201
    assert response.json()["job_type"] == "inference"
    call_args = mock_instance.execute_model_background.call_args
    assert call_args[1]["run_type"] == "infer"


def test_create_job_model_not_found(test_client: TestClient, mock_orchestrator):
    '''test creating a job with nonexistent model returns 404'''
    fake_id = str(uuid4())
    job_data = {
        "model_id": fake_id,
        "job_type": "training",
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    assert response.status_code == 404
    assert "model not found" in response.json()["detail"]


def test_create_job_model_not_installed(test_client: TestClient, mock_orchestrator):
    '''test creating a job against a non-installed model returns 400'''
    # create model but don't set status to installed
    model_data = {
        "name": f"pending-model-{uuid4().hex[:8]}",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True,
    }
    response = test_client.post("/api/v1/models", json=model_data)
    model_id = response.json()["id"]
    job_data = {
        "model_id": model_id,
        "job_type": "training",
    }
    response = test_client.post("/api/v1/jobs", json=job_data)
    assert response.status_code == 400
    assert "installed or active" in response.json()["detail"]


def test_list_jobs(test_client: TestClient, mock_orchestrator):
    '''test listing jobs'''
    _create_job(test_client)
    response = test_client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_job(test_client: TestClient, mock_orchestrator):
    '''test getting a job by id'''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["job_type"] == "training"


def test_get_job_not_found(test_client: TestClient, mock_orchestrator):
    '''test getting a nonexistent job returns 404'''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


def test_update_job(test_client: TestClient, mock_orchestrator):
    '''test updating a job'''
    job = _create_job(test_client)
    job_id = job["id"]
    update_data = {
        "status": "succeeded",
        "progress": 100,
    }
    response = test_client.patch(f"/api/v1/jobs/{job_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "succeeded"
    assert data["progress"] == 100


def test_update_job_not_found(test_client: TestClient, mock_orchestrator):
    '''test updating a nonexistent job returns 404'''
    fake_id = str(uuid4())
    response = test_client.patch(f"/api/v1/jobs/{fake_id}", json={"status": "running"})
    assert response.status_code == 404


def test_delete_job(test_client: TestClient, mock_orchestrator):
    '''test deleting a job'''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 404


def test_delete_job_not_found(test_client: TestClient, mock_orchestrator):
    '''test deleting a nonexistent job returns 404'''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


def test_get_job_logs(test_client: TestClient, mock_orchestrator):
    '''test getting logs for a job'''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_job_logs_not_found(test_client: TestClient, mock_orchestrator):
    '''test getting logs for a nonexistent job returns 404'''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}/logs")
    assert response.status_code == 404


def test_get_job_metrics(test_client: TestClient, mock_orchestrator):
    '''test getting metrics for a job'''
    job = _create_job(test_client)
    job_id = job["id"]
    response = test_client.get(f"/api/v1/jobs/{job_id}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_job_metrics_not_found(test_client: TestClient, mock_orchestrator):
    '''test getting metrics for a nonexistent job returns 404'''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/jobs/{fake_id}/metrics")
    assert response.status_code == 404


def test_internal_post_metric(test_client: TestClient, mock_orchestrator):
    '''test posting a training metric via internal endpoint (no auth)'''
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


def test_internal_post_metric_multiple(test_client: TestClient, mock_orchestrator):
    '''test posting multiple metrics for a job'''
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


def test_internal_post_log(test_client: TestClient, mock_orchestrator):
    '''test posting a log entry via internal endpoint (no auth)'''
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


def test_internal_post_log_multiple(test_client: TestClient, mock_orchestrator):
    '''test posting multiple logs for a job'''
    job = _create_job(test_client)
    job_id = job["id"]
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


def test_internal_post_metric_job_not_found(test_client: TestClient, mock_orchestrator):
    '''test posting metric for nonexistent job returns 404'''
    fake_id = str(uuid4())
    metric_data = {
        "job_id": fake_id,
        "metric_name": "loss",
        "metric_value": 0.5,
    }
    response = test_client.post(f"/api/v1/internal/metrics/{fake_id}", json=metric_data)
    assert response.status_code == 404


def test_internal_post_log_job_not_found(test_client: TestClient, mock_orchestrator):
    '''test posting log for nonexistent job returns 404'''
    fake_id = str(uuid4())
    log_data = {
        "job_id": fake_id,
        "message": "should fail",
        "level": "info",
    }
    response = test_client.post(f"/api/v1/internal/logs/{fake_id}", json=log_data)
    assert response.status_code == 404


def test_job_has_model_run_id(test_client: TestClient, mock_orchestrator):
    '''test that created job has model_run_id linking to the orchestrator run'''
    _, mock_run_id = mock_orchestrator
    job = _create_job(test_client)
    assert job["model_run_id"] == str(mock_run_id)


def test_logs_normalized_format(test_client: TestClient, mock_orchestrator):
    '''test that logs endpoint returns normalized format with job_id'''
    job = _create_job(test_client)
    job_id = job["id"]
    # post a log
    test_client.post(f"/api/v1/internal/logs/{job_id}", json={
        "message": "test log",
        "level": "info",
    })
    response = test_client.get(f"/api/v1/jobs/{job_id}/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    log = logs[0]
    assert "id" in log
    assert log["job_id"] == job_id
    assert log["level"] == "info"
    assert log["message"] == "test log"
    assert "created_at" in log
