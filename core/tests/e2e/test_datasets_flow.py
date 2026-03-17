'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for datasets management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_datasets_page_loads(page: Page, frontend_url: str):
    '''
    test that datasets page loads
    '''
    page.goto(f"{frontend_url}/datasets")
    page.wait_for_load_state("networkidle")
    assert "Datasets" in page.title() or "datasets" in page.content().lower()


def test_create_dataset_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating dataset via API and verifying in database
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {
        "name": ds_name,
        "description": "test dataset",
        "format": "csv"
    }

    response = requests.post(
        f"{backend_url}/api/v1/datasets",
        json=ds_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create dataset failed: {response.text}"
    dataset = response.json()
    ds_id = dataset["id"]

    db_ds = db_utils.query_generic("datasets", ds_id)
    assert db_ds is not None
    assert db_ds["name"] == ds_name
    assert db_ds["format"] == "csv"


def test_list_datasets_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing datasets via API
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {"name": ds_name, "format": "parquet"}
    requests.post(f"{backend_url}/api/v1/datasets", json=ds_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/datasets", headers=auth_headers)
    assert response.status_code == 200
    datasets = response.json()
    assert isinstance(datasets, list)
    assert len(datasets) > 0


def test_get_dataset_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting dataset by id
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {"name": ds_name, "format": "csv"}
    create_resp = requests.post(f"{backend_url}/api/v1/datasets", json=ds_data, headers=auth_headers)
    ds_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/datasets/{ds_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == ds_name


def test_update_dataset_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test updating dataset
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {"name": ds_name, "format": "csv"}
    create_resp = requests.post(f"{backend_url}/api/v1/datasets", json=ds_data, headers=auth_headers)
    ds_id = create_resp.json()["id"]

    update_resp = requests.patch(
        f"{backend_url}/api/v1/datasets/{ds_id}",
        json={"description": "updated description"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated description"


def test_delete_dataset_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a dataset
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {"name": ds_name, "format": "csv"}
    create_resp = requests.post(f"{backend_url}/api/v1/datasets", json=ds_data, headers=auth_headers)
    ds_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/datasets/{ds_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/datasets/{ds_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_dataset_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that dataset created via API appears in UI
    '''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    ds_data = {"name": ds_name, "format": "csv"}
    requests.post(f"{backend_url}/api/v1/datasets", json=ds_data, headers=auth_headers)

    page.goto(f"{frontend_url}/datasets")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={ds_name}").is_visible()
