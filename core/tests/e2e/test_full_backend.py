'''
Copyright 2019-Present The OpenUBA Platform Authors
Comprehensive backend e2e tests (Ingestion, Anomalies, Cases)
'''

import pytest
import requests
import time
from uuid import uuid4
from datetime import datetime

from core.tests.e2e.db_utils import DBTestUtils


def test_ingestion_api_flow(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    Test Data Ingestion Flow:
    Trigger Ingest -> Verify Run Created -> Verify Metrics (mocked/empty but endpoint works)
    '''
    # 1. Trigger Ingestion
    print("Step 1: Trigger Ingestion")
    dataset_name = "toy_1"
    ingest_payload = {
        "dataset_name": dataset_name,
        "ingest_to_spark": True,
        "ingest_to_es": True
    }
    
    response = requests.post(f"{backend_url}/api/v1/data/ingest", json=ingest_payload, timeout=15)
    if response.status_code != 200:
        print(f"Ingest trigger failed: {response.text}")
    
    # Ideally 200/202. The endpoint returns dict directly so 200 default.
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    run_id = data["run_id"]
    
    # 2. Verify DB Invariant
    print("Step 2: Verify DB Invariant (Ingestion Run)")
    # Process is background task, so we wait briefly
    time.sleep(2)
    runs = db_utils.get_data_ingestion_runs(dataset_name=dataset_name)
    assert len(runs) > 0, "Data ingestion run should be recorded in DB"
    
    # Verify specific run matches
    matching_run = next((r for r in runs if str(r["id"]) == run_id), None)
    assert matching_run is not None, "Returned run_id must exist in DB"
    
    # 3. Verify Metrics Endpoint
    print("Step 3: Verify Metrics Endpoint")
    metrics_resp = requests.get(f"{backend_url}/api/v1/data/metrics", timeout=15)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "spark" in metrics
    assert "elasticsearch" in metrics
    
    # 4. Verify History Endpoint
    print("Step 4: Verify History Endpoint")
    history_resp = requests.get(f"{backend_url}/api/v1/data/history?days=1", timeout=15)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert "history" in history


def test_anomaly_case_flow(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    Test Anomaly & Case Management Flow:
    Create Anomaly (via API) -> Search -> Create Case -> Link Anomaly -> Verify
    '''
    # 0. Create a Model for the Anomaly (Required FK)
    print("Step 0: Create Helper Model")
    model_name = f"anomaly_source_{uuid4().hex[:6]}"
    model_payload = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "dummy",
        "enabled": True
    }
    model_resp = requests.post(f"{backend_url}/api/v1/models", json=model_payload, timeout=15)
    assert model_resp.status_code == 201
    model_id = model_resp.json()["id"]

    # 1. Create Anomaly (Simulating detection)
    print("Step 1: Create Anomaly")
    entity_id = f"user_{uuid4().hex[:6]}"
    anomaly_payload = {
        "model_id": model_id,
        "entity_id": entity_id,
        "entity_type": "user",
        "risk_score": 85.0,
        "anomaly_type": "unusual_access",
        "details": {"location": "Mars"},
        "timestamp": datetime.now().isoformat(),
    }
    
    anomaly_resp = requests.post(f"{backend_url}/api/v1/anomalies", json=anomaly_payload, timeout=15)
    assert anomaly_resp.status_code == 201
    anomaly = anomaly_resp.json()
    anomaly_id = anomaly["id"]
    
    # 2. Verify Anomaly Search
    print("Step 2: Verify Anomaly Search")
    search_resp = requests.get(f"{backend_url}/api/v1/anomalies?entity_id={entity_id}", timeout=15)
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert len(search_results["items"]) > 0
    assert search_results["items"][0]["id"] == anomaly_id
    
    # 3. Create Case
    print("Step 3: Create Case")
    case_title = f"Investigation {uuid4().hex[:6]}"
    case_payload = {
        "title": case_title,
        "description": "Investigating suspicious Mars login",
        "severity": "high",
        "assigned_to": "admin"
    }
    
    case_resp = requests.post(f"{backend_url}/api/v1/cases", json=case_payload, timeout=15)
    assert case_resp.status_code == 201
    case = case_resp.json()
    case_id = case["id"]
    
    # 4. Link Anomaly to Case
    print("Step 4: Link Anomaly to Case")
    link_resp = requests.post(f"{backend_url}/api/v1/cases/{case_id}/anomalies/{anomaly_id}", timeout=15)
    assert link_resp.status_code == 200
    
    # 5. Verify DB Invariant (Case Anomaly Link)
    print("Step 5: Verify DB Invariant (Case Anomaly Link)")
    linked_anomalies = db_utils.get_case_anomalies(case_id)
    assert len(linked_anomalies) > 0, "Anomaly should be linked in DB"
    assert str(linked_anomalies[0]["id"]) == anomaly_id
    
    # 6. Update Case Status
    print("Step 6: Update Case Status")
    patch_resp = requests.patch(f"{backend_url}/api/v1/cases/{case_id}", json={"status": "resolved"}, timeout=15)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "resolved"
    
    # Verify DB Update
    print("Step 7: Verify DB Update")
    db_case = db_utils.query_case(case_id)
    assert db_case["status"] == "resolved"
    
    print("Anomaly & Case Flow Test Completed Successfully")
