'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for rules management flow
'''

import pytest
import requests
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_create_rule_via_api_and_verify(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test creating rule via api and verifying in database
    '''
    rule_name = f"e2e_test_rule_{uuid4().hex[:8]}"
    rule_data = {
        "name": rule_name,
        "description": "test rule",
        "rule_type": "single-fire",
        "condition": "risk_score > 80",
        "features": ["feature1", "feature2"],
        "score": 10,
        "enabled": True
    }
    
    response = requests.post(f"{backend_url}/api/v1/rules", json=rule_data)
    assert response.status_code == 201
    rule = response.json()
    rule_id = rule["id"]
    
    # verify in database
    db_rule = db_utils.query_rule(rule_id)
    assert db_rule is not None
    assert db_rule["name"] == rule_name
    assert db_rule["rule_type"] == "single-fire"


def test_list_rules_via_api(backend_url: str):
    '''
    test listing rules via api
    '''
    # create a rule
    rule_name = f"e2e_test_rule_{uuid4().hex[:8]}"
    rule_data = {
        "name": rule_name,
        "description": "test",
        "rule_type": "deviation",
        "condition": "value > threshold",
        "features": [],
        "score": 5,
        "enabled": True
    }
    requests.post(f"{backend_url}/api/v1/rules", json=rule_data)
    
    # list rules
    response = requests.get(f"{backend_url}/api/v1/rules")
    assert response.status_code == 200
    rules = response.json()
    assert isinstance(rules, list)
    assert len(rules) > 0


def test_update_rule_via_api(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test updating rule via api
    '''
    # create rule
    rule_name = f"e2e_test_rule_{uuid4().hex[:8]}"
    rule_data = {
        "name": rule_name,
        "description": "test",
        "rule_type": "single-fire",
        "condition": "test > 0",
        "features": [],
        "score": 1,
        "enabled": True
    }
    create_response = requests.post(f"{backend_url}/api/v1/rules", json=rule_data)
    rule_id = create_response.json()["id"]
    
    # update rule
    update_data = {
        "enabled": False,
        "score": 20
    }
    update_response = requests.patch(
        f"{backend_url}/api/v1/rules/{rule_id}",
        json=update_data
    )
    assert update_response.status_code == 200
    updated_rule = update_response.json()
    assert updated_rule["enabled"] == False
    assert updated_rule["score"] == 20
    
    # verify in database
    db_rule = db_utils.query_rule(rule_id)
    assert db_rule["enabled"] == False


def test_delete_rule_via_api(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test deleting rule via api
    '''
    # create rule
    rule_name = f"e2e_test_rule_{uuid4().hex[:8]}"
    rule_data = {
        "name": rule_name,
        "description": "test",
        "rule_type": "single-fire",
        "condition": "test > 0",
        "features": [],
        "score": 1,
        "enabled": True
    }
    create_response = requests.post(f"{backend_url}/api/v1/rules", json=rule_data)
    rule_id = create_response.json()["id"]
    
    # verify exists
    assert db_utils.query_rule(rule_id) is not None
    
    # delete rule
    delete_response = requests.delete(f"{backend_url}/api/v1/rules/{rule_id}")
    assert delete_response.status_code == 204
    
    # verify deleted
    get_response = requests.get(f"{backend_url}/api/v1/rules/{rule_id}")
    assert get_response.status_code == 404

