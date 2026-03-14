'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for sdk api router endpoints
'''

import pytest
import base64
from uuid import uuid4
from fastapi.testclient import TestClient


def _register_model_via_sdk(test_client: TestClient, name: str = None) -> dict:
    '''helper to register a model via SDK endpoint and return the response data'''
    body = {
        "name": name or f"sdk-model-{uuid4().hex[:8]}",
        "framework": "sklearn",
        "description": "model registered via SDK",
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    return response.json()


def test_sdk_register_model(test_client: TestClient):
    '''
    test registering a model via SDK endpoint
    '''
    body = {
        "name": "sdk-test-model",
        "framework": "sklearn",
        "description": "test model from SDK",
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "sdk-test-model"
    assert data["version"] == "1.0.0"
    assert data["slug"] == "sdk-test-model"
    assert "model_id" in data


def test_sdk_register_model_with_source_code(test_client: TestClient):
    '''
    test registering a model with base64-encoded source code
    '''
    source_code = "class Model:\n    def train(self, ctx):\n        pass\n"
    encoded = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
    body = {
        "name": f"sdk-code-model-{uuid4().hex[:8]}",
        "framework": "sklearn",
        "description": "model with source code",
        "source_code": encoded,
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    assert response.status_code == 200
    data = response.json()
    assert "model_id" in data


def test_sdk_register_model_duplicate(test_client: TestClient):
    '''
    test registering a model with duplicate name returns 400
    '''
    name = f"sdk-dup-model-{uuid4().hex[:8]}"
    test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
    })
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
    })
    assert response.status_code == 400


def test_sdk_register_model_invalid_base64(test_client: TestClient):
    '''
    test registering a model with invalid base64 returns 400
    '''
    body = {
        "name": f"sdk-bad-b64-{uuid4().hex[:8]}",
        "framework": "sklearn",
        "source_code": "not-valid-base64!!!",
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    assert response.status_code == 400


def test_sdk_publish_version(test_client: TestClient):
    '''
    test publishing a model version via SDK endpoint
    '''
    model = _register_model_via_sdk(test_client)
    model_id = model["model_id"]
    body = {
        "model_id": model_id,
        "version": "2.0.0",
        "summary": "improved accuracy",
    }
    response = test_client.post("/api/v1/sdk/publish-version", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == model_id
    assert data["version"] == "2.0.0"
    assert data["summary"] == "improved accuracy"
    assert "version_id" in data


def test_sdk_publish_version_model_not_found(test_client: TestClient):
    '''
    test publishing a version for nonexistent model returns 404
    '''
    fake_id = str(uuid4())
    body = {
        "model_id": fake_id,
        "version": "2.0.0",
    }
    response = test_client.post("/api/v1/sdk/publish-version", json=body)
    assert response.status_code == 404


def test_sdk_resolve_model(test_client: TestClient):
    '''
    test resolving a model by name
    '''
    name = f"sdk-resolve-model-{uuid4().hex[:8]}"
    _register_model_via_sdk(test_client, name=name)
    response = test_client.get(f"/api/v1/sdk/models/resolve/{name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["version"] == "1.0.0"
    assert "model_id" in data
    assert "slug" in data
    assert "source_type" in data


def test_sdk_resolve_model_not_found(test_client: TestClient):
    '''
    test resolving a nonexistent model returns 404
    '''
    response = test_client.get("/api/v1/sdk/models/resolve/nonexistent-model")
    assert response.status_code == 404
