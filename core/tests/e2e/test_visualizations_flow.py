'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for visualizations management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_visualizations_page_loads(page: Page, frontend_url: str):
    '''
    test that visualizations page loads
    '''
    page.goto(f"{frontend_url}/visualizations")
    page.wait_for_load_state("networkidle")
    assert "Visualizations" in page.title() or "visualizations" in page.content().lower()


def test_create_visualization_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating visualization via API and verifying in database
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {
        "name": viz_name,
        "backend": "recharts",
        "output_type": "html",
        "description": "test visualization",
        "config": {"chart_type": "bar"}
    }

    response = requests.post(
        f"{backend_url}/api/v1/visualizations",
        json=viz_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create viz failed: {response.text}"
    viz = response.json()
    viz_id = viz["id"]

    db_viz = db_utils.query_generic("visualizations", viz_id)
    assert db_viz is not None
    assert db_viz["name"] == viz_name
    assert db_viz["backend"] == "recharts"


def test_list_visualizations_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing visualizations via API
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "plotly", "output_type": "html"}
    requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/visualizations", headers=auth_headers)
    assert response.status_code == 200
    vizs = response.json()
    assert isinstance(vizs, list)
    assert len(vizs) > 0


def test_get_visualization_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting visualization by id
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "matplotlib", "output_type": "png"}
    create_resp = requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)
    viz_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/visualizations/{viz_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == viz_name


def test_update_visualization_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test updating visualization
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "recharts", "output_type": "html"}
    create_resp = requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)
    viz_id = create_resp.json()["id"]

    update_resp = requests.put(
        f"{backend_url}/api/v1/visualizations/{viz_id}",
        json={"name": f"{viz_name}_updated", "description": "updated desc"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated desc"


def test_publish_visualization_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test publishing a visualization
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "plotly", "output_type": "html"}
    create_resp = requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)
    viz_id = create_resp.json()["id"]

    pub_resp = requests.post(f"{backend_url}/api/v1/visualizations/{viz_id}/publish", headers=auth_headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["published"] == True

    # cannot publish again
    pub_resp2 = requests.post(f"{backend_url}/api/v1/visualizations/{viz_id}/publish", headers=auth_headers)
    assert pub_resp2.status_code == 400


def test_delete_visualization_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a visualization
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "recharts", "output_type": "html"}
    create_resp = requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)
    viz_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/visualizations/{viz_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/visualizations/{viz_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_visualization_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that visualization created via API appears in UI
    '''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    viz_data = {"name": viz_name, "backend": "recharts", "output_type": "html"}
    requests.post(f"{backend_url}/api/v1/visualizations", json=viz_data, headers=auth_headers)

    page.goto(f"{frontend_url}/visualizations")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={viz_name}").is_visible()
