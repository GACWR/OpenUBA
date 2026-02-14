'''
Copyright 2019-Present The OpenUBA Platform Authors
rules api router tests
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_create_rule(test_client: TestClient):
    '''
    test creating a rule
    '''
    rule_data = {
        "name": "test rule",
        "description": "test rule description",
        "rule_type": "single-fire",
        "condition": "risk_score > 80",
        "features": ["feature1", "feature2"],
        "score": 10.0,
        "enabled": True
    }
    response = test_client.post("/api/v1/rules", json=rule_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test rule"
    assert data["rule_type"] == "single-fire"
    assert "id" in data


def test_list_rules(test_client: TestClient):
    '''
    test listing rules
    '''
    # create a rule first
    rule_data = {
        "name": "list test rule",
        "description": "test",
        "rule_type": "deviation",
        "condition": "value > threshold",
        "features": [],
        "score": 5.0,
        "enabled": True
    }
    test_client.post("/api/v1/rules", json=rule_data)
    
    # list rules
    response = test_client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_rule(test_client: TestClient):
    '''
    test getting a rule by id
    '''
    # create a rule
    rule_data = {
        "name": "get test rule",
        "description": "test",
        "rule_type": "single-fire",
        "condition": "test > 0",
        "features": [],
        "score": 1.0,
        "enabled": True
    }
    create_response = test_client.post("/api/v1/rules", json=rule_data)
    rule_id = create_response.json()["id"]
    
    # get the rule
    response = test_client.get(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule_id
    assert data["name"] == "get test rule"

