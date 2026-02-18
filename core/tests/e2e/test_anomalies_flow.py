'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for anomaly detection and management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4
from datetime import datetime

from core.tests.e2e.db_utils import DBTestUtils


@pytest.fixture
def test_model(backend_url: str):
    '''
    create a test model for anomaly tests
    '''
    model_name = f"e2e_test_model_{uuid4().hex[:8]}"
    model_data = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    response = requests.post(f"{backend_url}/api/v1/models", json=model_data)
    assert response.status_code == 201
    return response.json()


def test_anomalies_page_loads(page: Page, frontend_url: str):
    '''
    test that anomalies page loads
    '''
    page.goto(f"{frontend_url}/anomalies")
    page.wait_for_load_state("networkidle")
    
    # check page has anomalies content
    assert "Anomalies" in page.title() or "anomalies" in page.content().lower()


def test_create_anomaly_via_api_and_verify(
    backend_url: str,
    db_utils: DBTestUtils,
    test_model: dict
):
    '''
    test creating anomaly via api and verifying in database
    '''
    entity_id = f"e2e_test_user_{uuid4().hex[:8]}"
    anomaly_data = {
        "model_id": test_model["id"],
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 85.5,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    
    response = requests.post(
        f"{backend_url}/api/v1/anomalies",
        json=anomaly_data
    )
    assert response.status_code == 201
    anomaly = response.json()
    anomaly_id = anomaly["id"]
    
    # verify in database
    db_anomaly = db_utils.query_anomaly(anomaly_id)
    assert db_anomaly is not None
    assert db_anomaly["entity_id"] == entity_id
    assert float(db_anomaly["risk_score"]) == 85.5


def test_list_anomalies_via_api(
    backend_url: str,
    test_model: dict
):
    '''
    test listing anomalies via api
    '''
    # create an anomaly
    entity_id = f"e2e_test_user_{uuid4().hex[:8]}"
    anomaly_data = {
        "model_id": test_model["id"],
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 75.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    requests.post(f"{backend_url}/api/v1/anomalies", json=anomaly_data)
    
    # list anomalies
    response = requests.get(f"{backend_url}/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_anomaly_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    test_model: dict
):
    '''
    test that anomaly created via api appears in ui
    '''
    # create anomaly
    entity_id = f"e2e_test_user_{uuid4().hex[:8]}"
    anomaly_data = {
        "model_id": test_model["id"],
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 90.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    requests.post(f"{backend_url}/api/v1/anomalies", json=anomaly_data)
    
    # check in ui
    page.goto(f"{frontend_url}/anomalies")
    page.wait_for_load_state("networkidle")
    
    # check entity id appears
    assert page.locator(f"text={entity_id}").is_visible()


def test_acknowledge_anomaly_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    test_model: dict
):
    '''
    test acknowledging anomaly via api
    '''
    # create anomaly
    entity_id = f"e2e_test_user_{uuid4().hex[:8]}"
    anomaly_data = {
        "model_id": test_model["id"],
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 80.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    create_response = requests.post(
        f"{backend_url}/api/v1/anomalies",
        json=anomaly_data
    )
    anomaly_id = create_response.json()["id"]
    
    # acknowledge anomaly
    ack_response = requests.post(
        f"{backend_url}/api/v1/anomalies/{anomaly_id}/acknowledge",
        params={"acknowledged_by": "e2e_test_analyst"}
    )
    assert ack_response.status_code == 200
    acknowledged = ack_response.json()
    assert acknowledged["acknowledged"] == True
    
    # verify in database
    db_anomaly = db_utils.query_anomaly(anomaly_id)
    assert db_anomaly["acknowledged"] == True


def test_filter_anomalies_by_risk_score(
    backend_url: str,
    test_model: dict
):
    '''
    test filtering anomalies by risk score
    '''
    # create anomalies with different risk scores
    for risk_score in [60.0, 70.0, 85.0, 95.0]:
        anomaly_data = {
            "model_id": test_model["id"],
            "entity_id": f"e2e_test_user_{uuid4().hex[:8]}",
            "entity_type": "user",
            "risk_score": risk_score,
            "anomaly_type": "behavioral",
            "timestamp": datetime.now().isoformat()
        }
        requests.post(f"{backend_url}/api/v1/anomalies", json=anomaly_data)
    
    # filter by min risk score
    response = requests.get(
        f"{backend_url}/api/v1/anomalies",
        params={"min_risk_score": 80.0}
    )
    assert response.status_code == 200
    data = response.json()
    # verify all returned anomalies have risk_score >= 80
    for anomaly in data["items"]:
        assert anomaly["risk_score"] >= 80.0

