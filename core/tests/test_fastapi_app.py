'''
Copyright 2019-Present The OpenUBA Platform Authors
fastapi app integration tests
'''

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(test_client: TestClient):
    '''
    test root endpoint returns api info
    '''
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["name"] == "OpenUBA API"
    assert data["version"] == "0.0.2"


def test_health_endpoint(test_client: TestClient):
    '''
    test health check endpoint
    '''
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_docs_available(test_client: TestClient):
    '''
    test that openapi docs are available
    '''
    response = test_client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(test_client: TestClient):
    '''
    test that openapi schema is available
    '''
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema

