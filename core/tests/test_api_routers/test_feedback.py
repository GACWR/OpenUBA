'''
Copyright 2019-Present The OpenUBA Platform Authors
feedback api router tests
'''

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient


def test_submit_feedback(test_client: TestClient):
    '''
    test submitting feedback on an anomaly
    '''
    # create model and anomaly first
    model_data = {
        "name": "feedback_test_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user_feedback",
        "entity_type": "user",
        "risk_score": 70.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    anomaly_response = test_client.post("/api/v1/anomalies", json=anomaly_data)
    anomaly_id = anomaly_response.json()["id"]
    
    # submit feedback
    feedback_data = {
        "anomaly_id": anomaly_id,
        "feedback_type": "true_positive",
        "notes": "confirmed anomaly",
        "user_id": "analyst1"
    }
    response = test_client.post("/api/v1/feedback", json=feedback_data)
    assert response.status_code == 201
    data = response.json()
    assert data["feedback_type"] == "true_positive"
    assert data["anomaly_id"] == anomaly_id
    assert "id" in data


def test_list_feedback(test_client: TestClient):
    '''
    test listing feedback for an anomaly
    '''
    # create model and anomaly
    model_data = {
        "name": "list_feedback_model",
        "version": "1.0.0",
        "source_type": "local_fs",
        "source_url": "test://model",
        "manifest": {},
        "enabled": True
    }
    model_response = test_client.post("/api/v1/models", json=model_data)
    model_id = model_response.json()["id"]
    
    anomaly_data = {
        "model_id": model_id,
        "entity_id": "user_list_feedback",
        "entity_type": "user",
        "risk_score": 65.0,
        "anomaly_type": "behavioral",
        "timestamp": datetime.now().isoformat()
    }
    anomaly_response = test_client.post("/api/v1/anomalies", json=anomaly_data)
    anomaly_id = anomaly_response.json()["id"]
    
    # submit feedback
    feedback_data = {
        "anomaly_id": anomaly_id,
        "feedback_type": "false_positive",
        "notes": "not an anomaly",
        "user_id": "analyst2"
    }
    test_client.post("/api/v1/feedback", json=feedback_data)
    
    # list feedback
    response = test_client.get(f"/api/v1/feedback?anomaly_id={anomaly_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

