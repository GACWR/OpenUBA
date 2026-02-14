'''
Copyright 2019-Present The OpenUBA Platform Authors
models api router tests
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_create_model(test_client: TestClient):
    '''
    test creating a model
    '''
    model_data = {
        "name": "test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {"test": "data"},
        "description": "test model",
        "author": "test author",
        "enabled": True
    }
    response = test_client.post("/api/v1/models", json=model_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_model"
    assert data["version"] == "1.0.0"
    assert "id" in data


def test_list_models(test_client: TestClient):
    '''
    test listing models
    '''
    # create a model first
    model_data = {
        "name": "list_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    test_client.post("/api/v1/models", json=model_data)
    
    # list models
    response = test_client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_model(test_client: TestClient):
    '''
    test getting a model by id
    '''
    # create a model
    model_data = {
        "name": "get_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    create_response = test_client.post("/api/v1/models", json=model_data)
    model_id = create_response.json()["id"]
    
    # get the model
    response = test_client.get(f"/api/v1/models/{model_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["name"] == "get_test_model"


def test_get_model_not_found(test_client: TestClient):
    '''
    test getting non-existent model
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/models/{fake_id}")
    assert response.status_code == 404


def test_update_model(test_client: TestClient):
    '''
    test updating a model
    '''
    # create a model
    model_data = {
        "name": "update_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    create_response = test_client.post("/api/v1/models", json=model_data)
    model_id = create_response.json()["id"]
    
    # update the model
    update_data = {"description": "updated description"}
    response = test_client.patch(f"/api/v1/models/{model_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "updated description"


def test_delete_model(test_client: TestClient):
    '''
    test deleting a model
    '''
    # create a model
    model_data = {
        "name": "delete_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    create_response = test_client.post("/api/v1/models", json=model_data)
    model_id = create_response.json()["id"]
    
    # delete the model
    response = test_client.delete(f"/api/v1/models/{model_id}")
    assert response.status_code == 204
    
    # verify it's deleted
    get_response = test_client.get(f"/api/v1/models/{model_id}")
    assert get_response.status_code == 404

