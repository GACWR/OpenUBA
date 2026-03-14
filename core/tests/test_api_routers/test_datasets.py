'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for datasets api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_dataset(test_client: TestClient, name: str = None) -> dict:
    '''helper to create a dataset and return the response data'''
    dataset_data = {
        "name": name or f"test-dataset-{uuid4().hex[:8]}",
        "description": "test dataset",
        "source_type": "upload",
        "format": "csv",
    }
    response = test_client.post("/api/v1/datasets", json=dataset_data)
    return response.json()


def test_create_dataset(test_client: TestClient):
    '''
    test creating a dataset
    '''
    dataset_data = {
        "name": "test-dataset",
        "description": "a test dataset",
        "source_type": "upload",
        "format": "csv",
    }
    response = test_client.post("/api/v1/datasets", json=dataset_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-dataset"
    assert data["description"] == "a test dataset"
    assert data["source_type"] == "upload"
    assert data["format"] == "csv"
    assert "id" in data


def test_create_dataset_defaults(test_client: TestClient):
    '''
    test creating a dataset with default values
    '''
    response = test_client.post("/api/v1/datasets", json={
        "name": "default-dataset",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "default-dataset"
    assert data["source_type"] == "upload"
    assert data["format"] == "csv"


def test_create_dataset_parquet(test_client: TestClient):
    '''
    test creating a parquet dataset
    '''
    response = test_client.post("/api/v1/datasets", json={
        "name": "parquet-dataset",
        "source_type": "s3",
        "format": "parquet",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "s3"
    assert data["format"] == "parquet"


def test_list_datasets(test_client: TestClient):
    '''
    test listing datasets
    '''
    _create_dataset(test_client)
    response = test_client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_dataset(test_client: TestClient):
    '''
    test getting a dataset by id
    '''
    dataset = _create_dataset(test_client, name="get-dataset-test")
    dataset_id = dataset["id"]
    response = test_client.get(f"/api/v1/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dataset_id
    assert data["name"] == "get-dataset-test"


def test_get_dataset_not_found(test_client: TestClient):
    '''
    test getting a nonexistent dataset returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/datasets/{fake_id}")
    assert response.status_code == 404


def test_update_dataset(test_client: TestClient):
    '''
    test updating a dataset
    '''
    dataset = _create_dataset(test_client)
    dataset_id = dataset["id"]
    update_data = {
        "name": "updated-dataset",
        "description": "updated description",
    }
    response = test_client.patch(f"/api/v1/datasets/{dataset_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-dataset"
    assert data["description"] == "updated description"


def test_update_dataset_not_found(test_client: TestClient):
    '''
    test updating a nonexistent dataset returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.patch(f"/api/v1/datasets/{fake_id}", json={"name": "nope"})
    assert response.status_code == 404


def test_delete_dataset(test_client: TestClient):
    '''
    test deleting a dataset
    '''
    dataset = _create_dataset(test_client)
    dataset_id = dataset["id"]
    response = test_client.delete(f"/api/v1/datasets/{dataset_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_resp.status_code == 404


def test_delete_dataset_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent dataset returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/datasets/{fake_id}")
    assert response.status_code == 404
