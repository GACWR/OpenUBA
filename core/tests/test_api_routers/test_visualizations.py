'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for visualizations api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_visualization(test_client: TestClient, name: str = None) -> dict:
    '''helper to create a visualization and return the response data'''
    viz_data = {
        "name": name or f"test-viz-{uuid4().hex[:8]}",
        "backend": "matplotlib",
        "output_type": "svg",
        "description": "test visualization",
        "code": "import matplotlib.pyplot as plt\nplt.plot([1,2,3])",
        "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "config": {"title": "test chart"},
        "refresh_interval": 60,
    }
    response = test_client.post("/api/v1/visualizations", json=viz_data)
    return response.json()


def test_create_visualization(test_client: TestClient):
    '''
    test creating a visualization
    '''
    viz_data = {
        "name": "test-visualization",
        "backend": "matplotlib",
        "output_type": "svg",
        "description": "a test chart",
        "code": "plt.plot([1,2,3])",
        "data": {"x": [1, 2, 3]},
        "config": {"title": "test"},
        "refresh_interval": 30,
    }
    response = test_client.post("/api/v1/visualizations", json=viz_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-visualization"
    assert data["backend"] == "matplotlib"
    assert data["output_type"] == "svg"
    assert data["description"] == "a test chart"
    assert data["refresh_interval"] == 30
    assert data["published"] is False
    assert "id" in data


def test_create_visualization_plotly(test_client: TestClient):
    '''
    test creating a plotly visualization
    '''
    viz_data = {
        "name": "plotly-viz",
        "backend": "plotly",
        "output_type": "plotly",
    }
    response = test_client.post("/api/v1/visualizations", json=viz_data)
    assert response.status_code == 201
    data = response.json()
    assert data["backend"] == "plotly"
    assert data["output_type"] == "plotly"


def test_list_visualizations(test_client: TestClient):
    '''
    test listing visualizations
    '''
    _create_visualization(test_client)
    response = test_client.get("/api/v1/visualizations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_visualization(test_client: TestClient):
    '''
    test getting a visualization by id
    '''
    viz = _create_visualization(test_client, name="get-viz-test")
    viz_id = viz["id"]
    response = test_client.get(f"/api/v1/visualizations/{viz_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == viz_id
    assert data["name"] == "get-viz-test"


def test_get_visualization_not_found(test_client: TestClient):
    '''
    test getting a nonexistent visualization returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/visualizations/{fake_id}")
    assert response.status_code == 404


def test_update_visualization(test_client: TestClient):
    '''
    test updating a visualization
    '''
    viz = _create_visualization(test_client)
    viz_id = viz["id"]
    update_data = {
        "name": "updated-viz",
        "description": "updated description",
        "code": "plt.bar([1,2,3], [4,5,6])",
        "refresh_interval": 120,
    }
    response = test_client.put(f"/api/v1/visualizations/{viz_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-viz"
    assert data["description"] == "updated description"
    assert data["refresh_interval"] == 120


def test_update_visualization_not_found(test_client: TestClient):
    '''
    test updating a nonexistent visualization returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.put(f"/api/v1/visualizations/{fake_id}", json={"name": "nope"})
    assert response.status_code == 404


def test_delete_visualization(test_client: TestClient):
    '''
    test deleting a visualization
    '''
    viz = _create_visualization(test_client)
    viz_id = viz["id"]
    response = test_client.delete(f"/api/v1/visualizations/{viz_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/visualizations/{viz_id}")
    assert get_resp.status_code == 404


def test_delete_visualization_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent visualization returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/visualizations/{fake_id}")
    assert response.status_code == 404


def test_publish_visualization(test_client: TestClient):
    '''
    test publishing a visualization
    '''
    viz = _create_visualization(test_client)
    viz_id = viz["id"]
    response = test_client.post(f"/api/v1/visualizations/{viz_id}/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["published"] is True


def test_publish_visualization_already_published(test_client: TestClient):
    '''
    test publishing an already published visualization returns 400
    '''
    viz = _create_visualization(test_client)
    viz_id = viz["id"]
    test_client.post(f"/api/v1/visualizations/{viz_id}/publish")
    response = test_client.post(f"/api/v1/visualizations/{viz_id}/publish")
    assert response.status_code == 400


def test_publish_visualization_not_found(test_client: TestClient):
    '''
    test publishing a nonexistent visualization returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.post(f"/api/v1/visualizations/{fake_id}/publish")
    assert response.status_code == 404
