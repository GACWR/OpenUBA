'''
Copyright 2019-Present The OpenUBA Platform Authors
display api router tests
'''

import pytest
from fastapi.testclient import TestClient


def test_get_home_summary(test_client: TestClient):
    '''
    test getting home dashboard summary
    '''
    response = test_client.get("/api/v1/display/home/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_models" in data
    assert "active_models" in data
    assert "total_anomalies" in data
    assert "unacknowledged_anomalies" in data
    assert "open_cases" in data
    assert isinstance(data["total_models"], int)
    assert isinstance(data["total_anomalies"], int)

