'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for pipelines api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_pipeline(test_client: TestClient, name: str = None) -> dict:
    '''helper to create a pipeline and return the response data'''
    pipeline_data = {
        "name": name or f"test-pipeline-{uuid4().hex[:8]}",
        "description": "test pipeline",
        "steps": [
            {"name": "ingest", "type": "data_source", "config": {"source": "csv"}},
            {"name": "transform", "type": "feature_engineering", "config": {}},
            {"name": "train", "type": "model_training", "config": {"model": "rf"}},
        ],
    }
    response = test_client.post("/api/v1/pipelines", json=pipeline_data)
    return response.json()


def test_create_pipeline(test_client: TestClient):
    '''
    test creating a pipeline
    '''
    pipeline_data = {
        "name": "test-pipeline",
        "description": "a test pipeline",
        "steps": [
            {"name": "step1", "type": "ingest"},
            {"name": "step2", "type": "train"},
        ],
    }
    response = test_client.post("/api/v1/pipelines", json=pipeline_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-pipeline"
    assert data["description"] == "a test pipeline"
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) == 2
    assert "id" in data


def test_create_pipeline_minimal(test_client: TestClient):
    '''
    test creating a pipeline with minimal fields
    '''
    response = test_client.post("/api/v1/pipelines", json={
        "name": "minimal-pipeline",
        "steps": [{"name": "only-step"}],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal-pipeline"
    assert data["description"] is None
    assert len(data["steps"]) == 1


def test_list_pipelines(test_client: TestClient):
    '''
    test listing pipelines
    '''
    _create_pipeline(test_client)
    response = test_client.get("/api/v1/pipelines")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_pipeline(test_client: TestClient):
    '''
    test getting a pipeline by id
    '''
    pipeline = _create_pipeline(test_client, name="get-pipeline-test")
    pipeline_id = pipeline["id"]
    response = test_client.get(f"/api/v1/pipelines/{pipeline_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pipeline_id
    assert data["name"] == "get-pipeline-test"


def test_get_pipeline_not_found(test_client: TestClient):
    '''
    test getting a nonexistent pipeline returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/pipelines/{fake_id}")
    assert response.status_code == 404


def test_update_pipeline(test_client: TestClient):
    '''
    test updating a pipeline
    '''
    pipeline = _create_pipeline(test_client)
    pipeline_id = pipeline["id"]
    update_data = {
        "name": "updated-pipeline",
        "description": "updated description",
        "steps": [
            {"name": "new-step-1", "type": "ingest"},
            {"name": "new-step-2", "type": "transform"},
            {"name": "new-step-3", "type": "train"},
            {"name": "new-step-4", "type": "evaluate"},
        ],
    }
    response = test_client.put(f"/api/v1/pipelines/{pipeline_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-pipeline"
    assert data["description"] == "updated description"
    assert len(data["steps"]) == 4


def test_update_pipeline_not_found(test_client: TestClient):
    '''
    test updating a nonexistent pipeline returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.put(f"/api/v1/pipelines/{fake_id}", json={
        "name": "nope",
        "steps": [],
    })
    assert response.status_code == 404


def test_delete_pipeline(test_client: TestClient):
    '''
    test deleting a pipeline
    '''
    pipeline = _create_pipeline(test_client)
    pipeline_id = pipeline["id"]
    response = test_client.delete(f"/api/v1/pipelines/{pipeline_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/pipelines/{pipeline_id}")
    assert get_resp.status_code == 404


def test_delete_pipeline_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent pipeline returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/pipelines/{fake_id}")
    assert response.status_code == 404


def test_run_pipeline(test_client: TestClient):
    '''
    test running a pipeline
    '''
    pipeline = _create_pipeline(test_client)
    pipeline_id = pipeline["id"]
    response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/run")
    assert response.status_code == 201
    data = response.json()
    assert data["pipeline_id"] == pipeline_id
    assert data["status"] == "pending"
    assert data["current_step"] == 0
    assert "id" in data


def test_run_pipeline_not_found(test_client: TestClient):
    '''
    test running a nonexistent pipeline returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.post(f"/api/v1/pipelines/{fake_id}/run")
    assert response.status_code == 404


def test_list_pipeline_runs(test_client: TestClient):
    '''
    test listing runs for a pipeline
    '''
    pipeline = _create_pipeline(test_client)
    pipeline_id = pipeline["id"]
    # run it twice
    test_client.post(f"/api/v1/pipelines/{pipeline_id}/run")
    test_client.post(f"/api/v1/pipelines/{pipeline_id}/run")
    response = test_client.get(f"/api/v1/pipelines/{pipeline_id}/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_list_pipeline_runs_not_found(test_client: TestClient):
    '''
    test listing runs for a nonexistent pipeline returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/pipelines/{fake_id}/runs")
    assert response.status_code == 404


def test_get_pipeline_run(test_client: TestClient):
    '''
    test getting a pipeline run by id
    '''
    pipeline = _create_pipeline(test_client)
    pipeline_id = pipeline["id"]
    run_resp = test_client.post(f"/api/v1/pipelines/{pipeline_id}/run")
    run_id = run_resp.json()["id"]
    response = test_client.get(f"/api/v1/pipelines/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run_id
    assert data["pipeline_id"] == pipeline_id


def test_get_pipeline_run_not_found(test_client: TestClient):
    '''
    test getting a nonexistent pipeline run returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/pipelines/runs/{fake_id}")
    assert response.status_code == 404
