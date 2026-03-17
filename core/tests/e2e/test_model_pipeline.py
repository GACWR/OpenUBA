'''
Copyright 2019-Present The OpenUBA Platform Authors
E2E test: model pipeline (notebook #9 simulation)

Registers an sklearn model via the SDK endpoint, submits training and inference
jobs pointing at the ES proxy index, polls until completion, and verifies that
both jobs succeed with expected outputs.

Requires a running OpenUBA cluster (make reset-dev).
Run with: pytest core/tests/e2e/test_model_pipeline.py -v -s
'''

import time
import pickle
import base64
import json
import logging
import pytest
import requests as http_requests

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def cleanup_test_data():
    '''override the conftest autouse cleanup — this test only uses HTTP APIs'''
    yield

POLL_INTERVAL = 5      # seconds between status polls
POLL_TIMEOUT = 120     # max seconds to wait for a job


def _poll_job(backend_url, job_id, headers, timeout=POLL_TIMEOUT):
    '''poll a job until it reaches a terminal state, return final job dict'''
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = http_requests.get(
            f"{backend_url}/api/v1/jobs/{job_id}",
            headers=headers,
        )
        assert resp.status_code == 200, f"failed to get job: {resp.text}"
        job = resp.json()
        status = job["status"]
        if status in ("succeeded", "failed", "cancelled"):
            return job
        time.sleep(POLL_INTERVAL)
    pytest.fail(f"job {job_id} did not finish within {timeout}s (last status: {status})")


def _get_job_logs(backend_url, job_id, headers):
    '''fetch logs for a job, return list of log dicts'''
    resp = http_requests.get(
        f"{backend_url}/api/v1/jobs/{job_id}/logs",
        headers=headers,
    )
    if resp.status_code == 200:
        return resp.json()
    return []


@pytest.fixture(scope="module")
def module_auth_headers(deployed_system):
    '''module-scoped auth headers so we only login once'''
    backend_url = deployed_system["backend_url"]
    resp = http_requests.post(
        f"{backend_url}/api/v1/auth/login",
        data={"username": "openuba", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def registered_model(deployed_system, module_auth_headers):
    '''
    register an sklearn IsolationForest model (simulating notebook #9).
    the pickle is intentionally created with the local sklearn version which
    may differ from the model-runner — the generated wrapper must handle this.
    '''
    backend_url = deployed_system["backend_url"]
    headers = {**module_auth_headers, "Content-Type": "application/json"}

    # create a fitted IsolationForest pickle (7 features like the notebook)
    from sklearn.ensemble import IsolationForest
    import numpy as np
    np.random.seed(42)
    X = np.random.randn(100, 7)
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(X)
    pkl_b64 = base64.b64encode(pickle.dumps(model)).decode()

    body = {
        "name": "E2E Pipeline Test Model",
        "framework": "sklearn",
        "description": "E2E test: sklearn IsolationForest for pipeline verification",
        "model_data": pkl_b64,
    }
    resp = http_requests.post(
        f"{backend_url}/api/v1/sdk/register-model",
        headers=headers,
        json=body,
    )
    assert resp.status_code == 200, f"register-model failed: {resp.text}"
    data = resp.json()
    assert "model_id" in data
    assert data["status"] == "installed"
    logger.info(f"registered model: {data['model_id']} ({data['name']})")
    return data


class TestModelPipeline:
    '''
    end-to-end model pipeline tests simulating notebook #9.
    tests run in order: register → train → infer.
    '''

    def test_training_job_succeeds(self, deployed_system, module_auth_headers, registered_model):
        '''submit a training job and verify it succeeds'''
        backend_url = deployed_system["backend_url"]
        headers = {**module_auth_headers, "Content-Type": "application/json"}
        model_id = registered_model["model_id"]

        # submit training job pointing at ES proxy index
        resp = http_requests.post(
            f"{backend_url}/api/v1/jobs",
            headers=headers,
            json={
                "name": "E2E Pipeline Training",
                "model_id": model_id,
                "job_type": "training",
                "input_data": {
                    "data_source": "elasticsearch",
                    "index_name": "openuba-proxy-toy_1",
                    "query": {"match_all": {}},
                },
            },
        )
        assert resp.status_code == 201, f"create job failed: {resp.text}"
        job = resp.json()
        job_id = job["id"]
        assert job["model_run_id"] is not None, "job should have a model_run_id"
        logger.info(f"training job created: {job_id}")

        # poll until complete
        final = _poll_job(backend_url, job_id, module_auth_headers)
        assert final["status"] == "succeeded", (
            f"training failed: {final.get('error_message')}\n"
            f"logs: {_get_job_logs(backend_url, job_id, module_auth_headers)}"
        )

        # verify training result in metrics
        metrics = final.get("metrics", {})
        training_result = metrics.get("training_result", {})
        assert training_result.get("status") == "success"
        assert training_result.get("n_samples", 0) > 0
        assert training_result.get("n_features", 0) > 0
        assert training_result.get("model_type") == "IsolationForest"

        # verify artifact was saved
        artifact_info = metrics.get("artifact_info", {})
        assert artifact_info.get("file_hash"), "artifact should have a file hash"
        assert artifact_info.get("path"), "artifact should have a path"

        # verify logs are available
        logs = _get_job_logs(backend_url, job_id, module_auth_headers)
        log_messages = [l["message"] for l in logs]
        assert any("Training completed" in m for m in log_messages), (
            f"expected 'Training completed' in logs, got: {log_messages}"
        )

        logger.info(
            f"training succeeded: {training_result['n_samples']} samples, "
            f"{training_result['n_features']} features"
        )

    def test_inference_job_succeeds(self, deployed_system, module_auth_headers, registered_model):
        '''submit an inference job (after training) and verify it succeeds with anomalies'''
        backend_url = deployed_system["backend_url"]
        headers = {**module_auth_headers, "Content-Type": "application/json"}
        model_id = registered_model["model_id"]

        # submit inference job
        resp = http_requests.post(
            f"{backend_url}/api/v1/jobs",
            headers=headers,
            json={
                "name": "E2E Pipeline Inference",
                "model_id": model_id,
                "job_type": "inference",
                "input_data": {
                    "data_source": "elasticsearch",
                    "index_name": "openuba-proxy-toy_1",
                    "query": {"match_all": {}},
                },
            },
        )
        assert resp.status_code == 201, f"create job failed: {resp.text}"
        job = resp.json()
        job_id = job["id"]
        assert job["model_run_id"] is not None
        logger.info(f"inference job created: {job_id}")

        # poll until complete
        final = _poll_job(backend_url, job_id, module_auth_headers)
        assert final["status"] == "succeeded", (
            f"inference failed: {final.get('error_message')}\n"
            f"logs: {_get_job_logs(backend_url, job_id, module_auth_headers)}"
        )

        # verify inference results
        metrics = final.get("metrics", {})
        assert metrics.get("status") == "success"
        anomaly_count = metrics.get("anomaly_count", 0)
        assert anomaly_count > 0, "inference should produce anomalies"

        # verify logs
        logs = _get_job_logs(backend_url, job_id, module_auth_headers)
        log_messages = [l["message"] for l in logs]
        assert any("inference complete" in m for m in log_messages), (
            f"expected 'inference complete' in logs, got: {log_messages}"
        )

        # verify artifact was loaded (not untrained)
        assert any("loaded sklearn artifact" in m for m in log_messages), (
            "inference should load the trained artifact from the training job"
        )

        logger.info(f"inference succeeded: {anomaly_count} anomalies detected")

    def test_job_logs_contain_expected_entries(self, deployed_system, module_auth_headers, registered_model):
        '''verify that job logs from previous runs are queryable'''
        backend_url = deployed_system["backend_url"]

        # list all jobs for this model
        resp = http_requests.get(
            f"{backend_url}/api/v1/jobs",
            headers=module_auth_headers,
            params={"model_id": registered_model["model_id"]},
        )
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) >= 2, "should have at least training + inference jobs"

        # verify each job has logs
        for job in jobs:
            logs = _get_job_logs(backend_url, job["id"], module_auth_headers)
            assert len(logs) > 0, f"job {job['id']} ({job['job_type']}) should have logs"
            logger.info(f"job {job['id']} ({job['job_type']}): {len(logs)} log entries")
