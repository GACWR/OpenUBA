'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for dashboards management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_dashboards_page_loads(page: Page, frontend_url: str):
    '''
    test that dashboards page loads
    '''
    page.goto(f"{frontend_url}/dashboards")
    page.wait_for_load_state("networkidle")
    assert "Dashboards" in page.title() or "dashboards" in page.content().lower()


def test_create_dashboard_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating dashboard via API
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {
        "name": dash_name,
        "description": "test dashboard",
        "layout": [{"columns": 2, "widgets": []}]
    }

    response = requests.post(
        f"{backend_url}/api/v1/dashboards",
        json=dash_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create dashboard failed: {response.text}"
    dashboard = response.json()
    dash_id = dashboard["id"]

    db_dash = db_utils.query_generic("dashboards", dash_id)
    assert db_dash is not None
    assert db_dash["name"] == dash_name


def test_list_dashboards_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing dashboards via API
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {"name": dash_name, "description": "test"}
    requests.post(f"{backend_url}/api/v1/dashboards", json=dash_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/dashboards", headers=auth_headers)
    assert response.status_code == 200
    dashboards = response.json()
    assert isinstance(dashboards, list)
    assert len(dashboards) > 0


def test_get_dashboard_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting dashboard by id
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {"name": dash_name, "description": "test"}
    create_resp = requests.post(f"{backend_url}/api/v1/dashboards", json=dash_data, headers=auth_headers)
    dash_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/dashboards/{dash_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == dash_name


def test_update_dashboard_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test updating dashboard
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {"name": dash_name, "description": "original"}
    create_resp = requests.post(f"{backend_url}/api/v1/dashboards", json=dash_data, headers=auth_headers)
    dash_id = create_resp.json()["id"]

    update_resp = requests.put(
        f"{backend_url}/api/v1/dashboards/{dash_id}",
        json={"description": "updated description"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated description"


def test_delete_dashboard_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a dashboard
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {"name": dash_name, "description": "to delete"}
    create_resp = requests.post(f"{backend_url}/api/v1/dashboards", json=dash_data, headers=auth_headers)
    dash_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/dashboards/{dash_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/dashboards/{dash_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_dashboard_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that dashboard created via API appears in UI
    '''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    dash_data = {"name": dash_name, "description": "ui test"}
    requests.post(f"{backend_url}/api/v1/dashboards", json=dash_data, headers=auth_headers)

    page.goto(f"{frontend_url}/dashboards")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={dash_name}").is_visible()
