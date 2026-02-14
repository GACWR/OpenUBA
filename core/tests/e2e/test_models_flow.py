'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for model management flow (API only)
'''

import pytest
import requests
import time
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils

# API-only tests for backend verification

def test_api_health_check(backend_url: str):
    '''
    test that backend is reachable
    '''
    response = requests.get(f"{backend_url}/api/v1/auth/users")
    # assuming auth/users or just root check. 
    # checking root might be safer:
    response = requests.get(f"{backend_url}/")
    assert response.status_code == 200


def test_full_model_lifecycle_api(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test complete model lifecycle via API:
    Search -> Register -> Install -> Train -> Execute -> Verify Jobs
    '''
    # 1. Search (Optional verification that search works)
    search_response = requests.get(f"{backend_url}/api/v1/models/search?query=dummy&registry_type=all")
    assert search_response.status_code == 200
    search_data = search_response.json()
    # verify we found our local dummy_model (if available in the env)
    # This might depend on what's in 'core/model_library'
    
    # 2. Register Model
    # We will register "dummy_model" which should be in the local_fs adapter
    model_name = f"e2e_test_model_{uuid4().hex[:8]}" 
    
    # Create physical model files for the runner to find
    import os
    from pathlib import Path
    import shutil
    
    # Assuming the test runs from project root or we can find core/model_library
    # Use relative path from known location
    base_path = Path("core/model_library")
    model_dir = base_path / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_code = """
class Model:
    def execute(self, data=None):
        return {"result": "success", "anomalies": []}
        
    def train(self, ctx):
        return {"accuracy": 0.99}
        
    def infer(self, ctx):
        import pandas as pd
        return pd.DataFrame([{"entity_id": "user_1", "risk_score": 90.0}])
"""
    with open(model_dir / "MODEL.py", "w") as f:
        f.write(model_code)
    
    model_data = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": model_name, # implies it's in core/model_library/{model_name}
        "enabled": True
    }
    
    register_response = requests.post(
        f"{backend_url}/api/v1/models",
        json=model_data
    )
    assert register_response.status_code == 201
    model = register_response.json()
    model_id = model["id"]
    
    # 3. Install Model
    install_response = requests.post(f"{backend_url}/api/v1/models/{model_id}/install")
    assert install_response.status_code == 200
    
    # Verify installation status via API
    get_model_response = requests.get(f"{backend_url}/api/v1/models/{model_id}")
    assert get_model_response.status_code == 200
    assert get_model_response.json()["status"] == "installed"

    # INVARIANT CHECK: Verify model_versions table has entries
    versions = db_utils.get_model_versions(model_id)
    assert len(versions) > 0, "Model version should be recorded in DB"
    assert versions[0]["version"] == "1.0.0"

    # 4. Train Model
    train_response = requests.post(f"{backend_url}/api/v1/models/{model_id}/train")
    # STRICT CHECK: Must be 200. If 500, it fails.
    assert train_response.status_code == 200, f"Training failed: {train_response.text}"
    job = train_response.json()
    assert "run_id" in job

    # INVARIANT CHECK: Verify model_runs table has a training job
    time.sleep(2)
    versions = db_utils.get_model_versions(model_id)
    assert len(versions) > 0, "Versions must exist to have runs"
    version_id = versions[0]["id"]
    
    runs = db_utils.get_model_runs(model_version_id=version_id)
    assert len(runs) > 0, "Model runs should be created"
    
    # 5. Execute (Infer) Model
    exec_response = requests.post(f"{backend_url}/api/v1/models/{model_id}/execute")
    assert exec_response.status_code == 200, f"Execution failed: {exec_response.text}"
    job = exec_response.json()
    assert "run_id" in job

    # INVARIANT CHECK: Verify model_runs table has an inference job
    time.sleep(2)
    runs = db_utils.get_model_runs(model_version_id=version_id)
    assert len(runs) >= 2, "Should have model_runs entries for train AND infer attempts"
    
    # 6. Verify Logs in DB
    logs = db_utils.get_execution_logs(model_id=model_id)
    assert len(logs) > 0, "Execution logs must exist"
    
    print(f"Verified {len(runs)} model runs and {len(logs)} execution logs.")
    
    # Clean up model files (optional, but good practice)
    try:
        shutil.rmtree(model_dir)
    except:
        pass

    print("Backend Model Lifecycle Test Completed with Invariant Checks")


def test_crud_model_api(
    backend_url: str,
    db_utils: DBTestUtils
):
    '''
    test basic CRUD operations via API
    '''
    # Create
    model_name = f"api_test_model_{uuid4().hex[:8]}"
    model_data = {
        "name": model_name,
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "enabled": True
    }
    
    resp = requests.post(f"{backend_url}/api/v1/models", json=model_data)
    assert resp.status_code == 201
    model_id = resp.json()["id"]
    
    # Read
    resp = requests.get(f"{backend_url}/api/v1/models/{model_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == model_name
    
    # Update
    resp = requests.patch(f"{backend_url}/api/v1/models/{model_id}", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["enabled"] == False
    
    # Delete
    resp = requests.delete(f"{backend_url}/api/v1/models/{model_id}")
    assert resp.status_code == 204
    
    # Verify Delete
    resp = requests.get(f"{backend_url}/api/v1/models/{model_id}")
    assert resp.status_code == 404


@pytest.mark.parametrize("model_name", [
    "model_sklearn",
    "model_pytorch",
    "model_tensorflow",
    "model_keras",
    "model_networkx"
])
def test_real_model_lifecycle(deployed_system, model_name, cleanup_test_data):
    """
    Test the full lifecycle for real implemented models.
    """
    api_url = deployed_system["backend_url"]
    
    # Setup: Copy model to unique directory to allow safe parallel/repeated testing
    import shutil
    from pathlib import Path
    
    unique_name = f"test_{model_name}_{uuid4().hex[:8]}"
    base_path = Path("core/model_library").resolve()
    src_dir = base_path / model_name
    dest_dir = base_path / unique_name
    
    # Ensure src exists
    assert src_dir.exists(), f"Source model {model_name} not found in library"
    
    # Copy
    shutil.copytree(src_dir, dest_dir)
    
    try:
        # 1. Register Model
        payload = {
            "name": unique_name,
            "version": "1.0.0",
            "model_name": unique_name, # Usually internal logic uses this
            "description": f"E2E Test for {model_name}",
            "mitre_tactic": "Defense Evasion",
            "mitre_technique_id": "T1070",
            "source_type": "local_fs",
            "source_url": unique_name, # Orchestrator uses Name, but ensuring alignment
            "enabled": True
        }
        
        response = requests.post(f"{api_url}/api/v1/models", json=payload)
        assert response.status_code == 201, f"Registration failed for {model_name}: {response.text}"
        model_data = response.json()
        model_id = model_data["id"]

        # 2. Install Model
        install_req = requests.post(f"{api_url}/api/v1/models/{model_id}/install")
        assert install_req.status_code == 200, f"Install failed: {install_req.text}"
        
        # Poll for READY/INSTALLED
        for _ in range(15):
            s_res = requests.get(f"{api_url}/api/v1/models/{model_id}")
            assert s_res.status_code == 200, f"Get status failed: {s_res.text}"
            if s_res.json()["status"] in ["installed", "ready"]:
                 break
            time.sleep(1)
            
        final_status = requests.get(f"{api_url}/api/v1/models/{model_id}").json()["status"]
        assert final_status in ["installed", "ready"], f"Model {model_name} failed to become installed/ready (got {final_status})"

        # 3. Train Model
        train_res = requests.post(f"{api_url}/api/v1/models/{model_id}/train") 
        assert train_res.status_code == 200, f"Training trigger failed: {train_res.text}"
        train_job = train_res.json()
        assert "run_id" in train_job

        # Wait for completion
        # TF/Torch training might take a bit
        for _ in range(90):  # 90s timeout
            j_res = requests.get(f"{api_url}/api/v1/models/runs/{train_job['run_id']}")
            status = j_res.json()["status"]
            if status in ["completed", "failed", "error"]:
                assert status == "completed", f"Training failed for {model_name}: {j_res.json().get('error_message', 'No error msg')}"
                break
            time.sleep(1)
            
        final_status = requests.get(f"{api_url}/api/v1/models/runs/{train_job['run_id']}").json()["status"]
        assert final_status == "completed", f"Training timed out or failed for {model_name}"

        # 4. Execute (Infer) Model
        exec_res = requests.post(f"{api_url}/api/v1/models/{model_id}/execute", json={"data": []})
        assert exec_res.status_code == 200, f"Execution trigger failed: {exec_res.text}"
        exec_job = exec_res.json()
        assert "run_id" in exec_job
        
        for _ in range(60):
            j_res = requests.get(f"{api_url}/api/v1/models/runs/{exec_job['run_id']}")
            status = j_res.json()["status"]
            if status in ["completed", "failed", "error"]:
                 assert status == "completed", f"Execution failed for {model_name}: {j_res.json().get('error_message', 'No error msg')}"
                 break
            time.sleep(1)
            
        final_infer_status = requests.get(f"{api_url}/api/v1/models/runs/{exec_job['run_id']}").json()["status"]
        assert final_infer_status == "completed", f"Inference timed out or failed for {model_name}"

    finally:
        # Cleanup
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

