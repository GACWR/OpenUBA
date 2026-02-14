
import pytest
import requests
import time
import shutil
from pathlib import Path
from uuid import uuid4

# The matrix of models to test
# These correspond to the directories in core/model_library/
MODELS = [
    "model_sklearn",
    "model_pytorch",
    "model_tensorflow",
    "model_keras", 
    "model_networkx"
]

# The datasets to verify against
DATASETS = ["toy_1"]

@pytest.fixture(scope="module")
def api_url(deployed_system):
    return deployed_system["backend_url"]

@pytest.fixture(scope="module")
def setup_dataset(api_url):
    """
    Ensure toy_1 is ingested and available.
    """
    # Check if dataset exists
    # If not, ingest (although k8s-init-data usually does this)
    # For now, we assume it's there or we treat it as a prerequisite.
    pass

@pytest.mark.parametrize("model_name", MODELS)
@pytest.mark.parametrize("dataset_name", DATASETS)
def test_jit_model_matrix(api_url, model_name, dataset_name):
    """
    Verify that each model type can correctly:
    1. Register/Install (Singleton - Reuse if exists)
    2. Train (JIT job on K8s)
    3. Infer (JIT job on K8s)
    targeting specific datasets.
    """
    # Deterministic name representing Model + Config (Dataset)
    unique_name = f"jit_{model_name}_{dataset_name}"
    print(f"\n⚡️ TESTING JIT MATRIX: {unique_name}")
    
    # 1. Check if model already exists (Singleton Pattern)
    # The user wants to reuse models like 'test_model_keras_proxy_toy'
    existing_models = requests.get(f"{api_url}/api/v1/models?limit=1000").json()
    target_model = next((m for m in existing_models if m["name"] == unique_name), None)
    
    model_id = None
    if target_model:
        print(f"  -> Model {unique_name} already exists. Reusing.")
        model_id = target_model["id"]
        # Ensure it is installed
        if target_model["status"] != "installed":
             requests.post(f"{api_url}/api/v1/models/{model_id}/install")
    else:
        print(f"  -> Registering new singleton {unique_name}...")
        base_library_path = Path("core/model_library").resolve()
        src_dir = base_library_path / model_name
        
        # Derive runtime from model_name
        runtime = model_name.replace("model_", "")
        if runtime == "keras":
            runtime = "tensorflow"
            
        payload = {
            "name": unique_name,
            "version": "1.0.0",
            "model_name": unique_name,
            "description": f"JIT E2E Test for {model_name} on {dataset_name}",
            "source_type": "local_fs",
            "source_url": str(src_dir), # Point to the CANONICAL source code
            "enabled": True,
            "runtime": runtime
        }
        
        resp = requests.post(f"{api_url}/api/v1/models", json=payload)
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        model_id = resp.json()["id"]
        
        # Install
        print(f"  -> Installing {unique_name}...")
        resp = requests.post(f"{api_url}/api/v1/models/{model_id}/install")
        assert resp.status_code == 200

    # Poll for installation (idempotent)
    for _ in range(30):
        status = requests.get(f"{api_url}/api/v1/models/{model_id}").json()["status"]
        if status in ["installed", "ready"]:
            break
        time.sleep(1)
    assert status in ["installed", "ready"], f"Install timed out. Status: {status}"
    
    # 2. Train
    print(f"  -> Training {unique_name}...")
    # Trigger training. Usage of dataset_name logic would go into config here.
    resp = requests.post(f"{api_url}/api/v1/models/{model_id}/train")
    if resp.status_code != 200:
         print(f"Train failed: {resp.text}")
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    
    # Poll for completion (Wait longer for TF/Torch)
    final_status = wait_for_run(api_url, run_id, timeout=120)
    assert final_status == "completed", f"Training failed! Run: {run_id}"
    
    # 3. Inference (with Data)
    print(f"  -> Inferencing {unique_name}...")
    mock_data = [
        {"entity_id": "user_1", "col1": 0.5, "col2": 1.2, "value": 100},
        {"entity_id": "user_2", "col1": 0.1, "col2": 0.2, "value": 10},
        {"entity_id": "user_3", "col1": 0.9, "col2": 3.5, "value": 500}
    ]
    
    resp = requests.post(f"{api_url}/api/v1/models/{model_id}/execute", json={"data": mock_data})
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    
    human_status = wait_for_run(api_url, run_id, timeout=60)
    assert human_status == "completed", f"Inference failed! Run: {run_id}"
    
    print(f"✅ VERIFIED: {unique_name}")


def wait_for_run(api_url, run_id, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{api_url}/api/v1/models/runs/{run_id}")
        if resp.status_code != 200:
            return "error"
        data = resp.json()
        if data["status"] in ["completed", "failed", "error"]:
            if data["status"] != "completed":
                print(f"    [Run Error details]: {data.get('error_message')}")
            return data["status"]
        time.sleep(2)
    return "timeout"
