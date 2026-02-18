'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for case management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4
from datetime import datetime

from core.tests.e2e.db_utils import DBTestUtils


@pytest.fixture
def test_model_and_anomaly(backend_url: str):
    '''
    create test model and anomaly for case tests
    '''
    # create model
    model_name = f"e2e_test_model_{uuid4().hex[:8]}"
    model_data = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = requests.post(f"{backend_url}/api/v1/models", json=model_data)
    model = model_response.json()
    
    # create anomaly
    entity_id = f"e2e_test_user_{uuid4().hex[:8]}"
    anomaly_data = {
        "model_id": model["id"],
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 90.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    anomaly_response = requests.post(
        f"{backend_url}/api/v1/anomalies",
        json=anomaly_data
    )
    anomaly = anomaly_response.json()
    
    return {"model": model, "anomaly": anomaly}


def test_cases_page_loads(page: Page, frontend_url: str):
    '''
    test that cases page loads
    '''
    page.goto(f"{frontend_url}/cases")
    page.wait_for_load_state("networkidle")
    
    # check page has cases content
    assert "Cases" in page.title() or "cases" in page.content().lower()


def test_create_case_via_api_and_verify(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test creating case via api and verifying in database
    '''
    case_title = f"e2e_test_case_{uuid4().hex[:8]}"
    case_data = {
        "title": case_title,
        "description": "test case description",
        "severity": "high",
        "analyst_notes": "initial notes"
    }
    
    response = requests.post(f"{backend_url}/api/v1/cases", json=case_data)
    assert response.status_code == 201
    case = response.json()
    case_id = case["id"]
    
    # verify in database
    db_case = db_utils.query_case(case_id)
    assert db_case is not None
    assert db_case["title"] == case_title
    assert db_case["status"] == "open"
    assert db_case["severity"] == "high"


def test_list_cases_via_api(backend_url: str):
    '''
    test listing cases via api
    '''
    # create a case
    case_title = f"e2e_test_case_{uuid4().hex[:8]}"
    case_data = {
        "title": case_title,
        "description": "test",
        "severity": "medium"
    }
    requests.post(f"{backend_url}/api/v1/cases", json=case_data)
    
    # list cases
    response = requests.get(f"{backend_url}/api/v1/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) > 0


def test_link_anomaly_to_case_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    test_model_and_anomaly: dict
):
    '''
    test linking anomaly to case via api
    '''
    # create case
    case_title = f"e2e_test_case_{uuid4().hex[:8]}"
    case_data = {
        "title": case_title,
        "description": "test case",
        "severity": "high"
    }
    case_response = requests.post(f"{backend_url}/api/v1/cases", json=case_data)
    case_id = case_response.json()["id"]
    
    # link anomaly
    anomaly_id = test_model_and_anomaly["anomaly"]["id"]
    link_response = requests.post(
        f"{backend_url}/api/v1/cases/{case_id}/anomalies/{anomaly_id}"
    )
    assert link_response.status_code == 200
    
    # verify in database
    linked_anomalies = db_utils.get_case_anomalies(case_id)
    assert len(linked_anomalies) > 0
    # check if anomaly is linked (compare as strings since UUIDs might be returned differently)
    anomaly_ids = [str(a.get("id", "")) for a in linked_anomalies]
    assert str(anomaly_id) in anomaly_ids


def test_update_case_via_api(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test updating case via api
    '''
    # create case
    case_title = f"e2e_test_case_{uuid4().hex[:8]}"
    case_data = {
        "title": case_title,
        "description": "initial description",
        "severity": "medium"
    }
    create_response = requests.post(f"{backend_url}/api/v1/cases", json=case_data)
    case_id = create_response.json()["id"]
    
    # update case
    update_data = {
        "status": "investigating",
        "analyst_notes": "updated notes"
    }
    update_response = requests.patch(
        f"{backend_url}/api/v1/cases/{case_id}",
        json=update_data
    )
    assert update_response.status_code == 200
    updated_case = update_response.json()
    assert updated_case["status"] == "investigating"
    
    # verify in database
    db_case = db_utils.query_case(case_id)
    assert db_case["status"] == "investigating"


def test_case_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str
):
    '''
    test that case created via api appears in ui
    '''
    # create case
    case_title = f"e2e_test_case_{uuid4().hex[:8]}"
    case_data = {
        "title": case_title,
        "description": "test case",
        "severity": "high"
    }
    requests.post(f"{backend_url}/api/v1/cases", json=case_data)
    
    # check in ui
    page.goto(f"{frontend_url}/cases")
    page.wait_for_load_state("networkidle")
    
    # check case appears
    assert page.locator(f"text={case_title}").is_visible()

