'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for dashboards api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_dashboard(test_client: TestClient, name: str = None) -> dict:
    '''helper to create a dashboard and return the response data'''
    dashboard_data = {
        "name": name or f"test-dashboard-{uuid4().hex[:8]}",
        "description": "test dashboard",
        "layout": [
            {"type": "chart", "viz_id": str(uuid4()), "position": {"x": 0, "y": 0}},
            {"type": "chart", "viz_id": str(uuid4()), "position": {"x": 1, "y": 0}},
        ],
    }
    response = test_client.post("/api/v1/dashboards", json=dashboard_data)
    return response.json()


def test_create_dashboard(test_client: TestClient):
    '''
    test creating a dashboard
    '''
    dashboard_data = {
        "name": "test-dashboard",
        "description": "a test dashboard",
        "layout": [{"type": "chart", "position": {"x": 0, "y": 0}}],
    }
    response = test_client.post("/api/v1/dashboards", json=dashboard_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-dashboard"
    assert data["description"] == "a test dashboard"
    assert data["published"] is False
    assert isinstance(data["layout"], list)
    assert len(data["layout"]) == 1
    assert "id" in data


def test_create_dashboard_minimal(test_client: TestClient):
    '''
    test creating a dashboard with only required fields
    '''
    response = test_client.post("/api/v1/dashboards", json={
        "name": "minimal-dashboard",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal-dashboard"
    assert data["description"] is None


def test_list_dashboards(test_client: TestClient):
    '''
    test listing dashboards
    '''
    _create_dashboard(test_client)
    response = test_client.get("/api/v1/dashboards")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_dashboard(test_client: TestClient):
    '''
    test getting a dashboard by id
    '''
    dashboard = _create_dashboard(test_client, name="get-dash-test")
    dash_id = dashboard["id"]
    response = test_client.get(f"/api/v1/dashboards/{dash_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dash_id
    assert data["name"] == "get-dash-test"


def test_get_dashboard_not_found(test_client: TestClient):
    '''
    test getting a nonexistent dashboard returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/dashboards/{fake_id}")
    assert response.status_code == 404


def test_update_dashboard(test_client: TestClient):
    '''
    test updating a dashboard
    '''
    dashboard = _create_dashboard(test_client)
    dash_id = dashboard["id"]
    update_data = {
        "name": "updated-dashboard",
        "description": "updated description",
        "layout": [{"type": "table", "position": {"x": 0, "y": 0}}],
    }
    response = test_client.put(f"/api/v1/dashboards/{dash_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-dashboard"
    assert data["description"] == "updated description"
    assert len(data["layout"]) == 1


def test_update_dashboard_not_found(test_client: TestClient):
    '''
    test updating a nonexistent dashboard returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.put(f"/api/v1/dashboards/{fake_id}", json={"name": "nope"})
    assert response.status_code == 404


def test_delete_dashboard(test_client: TestClient):
    '''
    test deleting a dashboard
    '''
    dashboard = _create_dashboard(test_client)
    dash_id = dashboard["id"]
    response = test_client.delete(f"/api/v1/dashboards/{dash_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/dashboards/{dash_id}")
    assert get_resp.status_code == 404


def test_delete_dashboard_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent dashboard returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/dashboards/{fake_id}")
    assert response.status_code == 404
