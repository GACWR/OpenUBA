'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for experiments api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_experiment(test_client: TestClient, name: str = None) -> dict:
    '''helper to create an experiment and return the response data'''
    experiment_data = {
        "name": name or f"test-experiment-{uuid4().hex[:8]}",
        "description": "test experiment",
    }
    response = test_client.post("/api/v1/experiments", json=experiment_data)
    return response.json()


def _create_experiment_run(test_client: TestClient, experiment_id: str) -> dict:
    '''helper to add a run to an experiment'''
    run_data = {
        "experiment_id": experiment_id,
        "parameters": {"learning_rate": 0.01, "batch_size": 32},
        "metrics": {"accuracy": 0.85, "loss": 0.3},
    }
    response = test_client.post(
        f"/api/v1/experiments/{experiment_id}/runs", json=run_data
    )
    return response.json()


def test_create_experiment(test_client: TestClient):
    '''
    test creating an experiment
    '''
    experiment_data = {
        "name": "test-experiment",
        "description": "testing experiment tracking",
    }
    response = test_client.post("/api/v1/experiments", json=experiment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-experiment"
    assert data["description"] == "testing experiment tracking"
    assert "id" in data
    assert "created_at" in data


def test_create_experiment_minimal(test_client: TestClient):
    '''
    test creating an experiment with only required fields
    '''
    response = test_client.post("/api/v1/experiments", json={
        "name": "minimal-experiment",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal-experiment"
    assert data["description"] is None


def test_list_experiments(test_client: TestClient):
    '''
    test listing experiments
    '''
    _create_experiment(test_client)
    response = test_client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_experiment(test_client: TestClient):
    '''
    test getting an experiment by id
    '''
    experiment = _create_experiment(test_client, name="get-exp-test")
    exp_id = experiment["id"]
    response = test_client.get(f"/api/v1/experiments/{exp_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exp_id
    assert data["name"] == "get-exp-test"


def test_get_experiment_not_found(test_client: TestClient):
    '''
    test getting a nonexistent experiment returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/experiments/{fake_id}")
    assert response.status_code == 404


def test_delete_experiment(test_client: TestClient):
    '''
    test deleting an experiment
    '''
    experiment = _create_experiment(test_client)
    exp_id = experiment["id"]
    response = test_client.delete(f"/api/v1/experiments/{exp_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/experiments/{exp_id}")
    assert get_resp.status_code == 404


def test_delete_experiment_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent experiment returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/experiments/{fake_id}")
    assert response.status_code == 404


def test_add_experiment_run(test_client: TestClient):
    '''
    test adding a run to an experiment
    '''
    experiment = _create_experiment(test_client)
    exp_id = experiment["id"]
    run_data = {
        "experiment_id": exp_id,
        "parameters": {"learning_rate": 0.001, "epochs": 50},
        "metrics": {"accuracy": 0.92, "f1_score": 0.88},
    }
    response = test_client.post(f"/api/v1/experiments/{exp_id}/runs", json=run_data)
    assert response.status_code == 201
    data = response.json()
    assert data["experiment_id"] == exp_id
    assert data["parameters"]["learning_rate"] == 0.001
    assert data["metrics"]["accuracy"] == 0.92
    assert data["status"] == "pending"
    assert "id" in data


def test_add_experiment_run_not_found(test_client: TestClient):
    '''
    test adding a run to a nonexistent experiment returns 404
    '''
    fake_id = str(uuid4())
    run_data = {
        "experiment_id": fake_id,
        "parameters": {},
    }
    response = test_client.post(f"/api/v1/experiments/{fake_id}/runs", json=run_data)
    assert response.status_code == 404


def test_list_experiment_runs(test_client: TestClient):
    '''
    test listing runs for an experiment
    '''
    experiment = _create_experiment(test_client)
    exp_id = experiment["id"]
    # add two runs
    _create_experiment_run(test_client, exp_id)
    _create_experiment_run(test_client, exp_id)
    response = test_client.get(f"/api/v1/experiments/{exp_id}/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_list_experiment_runs_not_found(test_client: TestClient):
    '''
    test listing runs for a nonexistent experiment returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/experiments/{fake_id}/runs")
    assert response.status_code == 404


def test_update_experiment_run(test_client: TestClient):
    '''
    test updating an experiment run
    '''
    experiment = _create_experiment(test_client)
    exp_id = experiment["id"]
    run = _create_experiment_run(test_client, exp_id)
    run_id = run["id"]
    update_data = {
        "experiment_id": exp_id,
        "metrics": {"accuracy": 0.95, "loss": 0.1},
    }
    response = test_client.patch(f"/api/v1/experiments/runs/{run_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["accuracy"] == 0.95


def test_update_experiment_run_not_found(test_client: TestClient):
    '''
    test updating a nonexistent experiment run returns 404
    '''
    fake_id = str(uuid4())
    update_data = {
        "experiment_id": str(uuid4()),
        "metrics": {"accuracy": 0.5},
    }
    response = test_client.patch(f"/api/v1/experiments/runs/{fake_id}", json=update_data)
    assert response.status_code == 404


def test_compare_experiment_runs(test_client: TestClient):
    '''
    test comparing experiment runs
    '''
    experiment = _create_experiment(test_client)
    exp_id = experiment["id"]
    # add multiple runs with different metrics
    for lr in [0.01, 0.001, 0.0001]:
        run_data = {
            "experiment_id": exp_id,
            "parameters": {"learning_rate": lr},
            "metrics": {"accuracy": 0.8 + lr, "loss": 0.5 - lr},
        }
        test_client.post(f"/api/v1/experiments/{exp_id}/runs", json=run_data)

    response = test_client.get(f"/api/v1/experiments/{exp_id}/compare")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_compare_experiment_runs_not_found(test_client: TestClient):
    '''
    test comparing runs for a nonexistent experiment returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/experiments/{fake_id}/compare")
    assert response.status_code == 404
