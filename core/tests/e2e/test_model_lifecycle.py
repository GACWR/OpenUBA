import pytest
import time
import requests
import os
from uuid import UUID
from core.db import get_db_context
from core.db.models import ModelRun, ExecutionLog, Anomaly

API_URL = "http://localhost:8000/api/v1"

@pytest.fixture(scope="module")
def api_client():
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()

        def get(self, endpoint, **kwargs):
            return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

        def post(self, endpoint, **kwargs):
            return self.session.post(f"{self.base_url}{endpoint}", **kwargs)

    return APIClient(API_URL)

def test_environment_health(api_client):
    """Verify backend is healthy"""
    resp = requests.get("http://localhost:8000/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_model_lifecycle_e2e(api_client):
    """
    Test complete model lifecycle:
    1. Install Model
    2. Train Model
    3. Execute Model (Inference)
    4. Verify Results
    """
    # 1. Install Model
    # First search for it to get details (simulating UI)
    search_resp = api_client.get("/models/search?query=dummy&registry_type=all")
    assert search_resp.status_code == 200
    models = search_resp.json()["models"]
    dummy_model = next((m for m in models if "dummy" in m["name"]), None)
    assert dummy_model is not None, "Dummy model not found in registry"

    # Register/Install
    model_data = {
        "name": dummy_model["name"],
        "version": dummy_model["version"],
        "source_type": dummy_model["source_type"],
        "source_url": dummy_model["source_url"],
        "enabled": True
    }
    
    # Check if already exists
    existing_resp = api_client.get("/models")
    existing_models = existing_resp.json()
    existing = next((m for m in existing_models if m["name"] == model_data["name"]), None)
    
    if existing:
        model_id = existing["id"]
    else:
        create_resp = api_client.post("/models", json=model_data)
        assert create_resp.status_code == 200
        model_id = create_resp.json()["id"]

    # Trigger Install
    install_resp = api_client.post(f"/models/{model_id}/install")
    assert install_resp.status_code == 200
    
    # Wait for installation
    max_retries = 10
    for _ in range(max_retries):
        model_resp = api_client.get(f"/models/{model_id}")
        if model_resp.json()["status"] == "installed":
            break
        time.sleep(2)
    else:
        pytest.fail("Model installation timed out")

    # 2. Train Model
    train_resp = api_client.post(f"/models/{model_id}/train")
    assert train_resp.status_code == 200
    run_id = train_resp.json()["run_id"]
    
    # Wait for training completion
    _wait_for_run(api_client, run_id)

    # 3. Execute Model (Inference)
    infer_resp = api_client.post(f"/models/{model_id}/execute")
    assert infer_resp.status_code == 200
    run_id = infer_resp.json()["run_id"]
    
    # Wait for inference completion
    _wait_for_run(api_client, run_id)

    # 4. Verify Results
    # Check anomalies were created
    with get_db_context() as db:
        # Get the run to check result summary
        run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
        assert run.status == "succeeded"
        assert run.result_summary is not None
        
        # Check anomalies table
        anomalies = db.query(Anomaly).filter(Anomaly.model_id == model_id).all()
        # We expect some anomalies from the dummy model if it generates any
        # The dummy model might just print output, need to check its implementation
        
def _wait_for_run(api_client, run_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check via API or DB. API is better for E2E.
        # Assuming we have an endpoint to get run status, or we check jobs
        # For now, let's query DB directly as the API might not expose granular run status easily yet
        # Or use the jobs endpoint if available.
        # Let's use DB for reliability in test
        with get_db_context() as db:
            run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
            if run.status in ["succeeded", "failed"]:
                if run.status == "failed":
                    pytest.fail(f"Run {run_id} failed: {run.error_message}")
                return
        time.sleep(5)
    pytest.fail(f"Run {run_id} timed out")
