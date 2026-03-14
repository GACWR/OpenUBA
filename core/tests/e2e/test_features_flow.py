'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for feature store management flow
'''

import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

from core.tests.e2e.db_utils import DBTestUtils


def test_features_page_loads(page: Page, frontend_url: str):
    '''
    test that features page loads
    '''
    page.goto(f"{frontend_url}/features")
    page.wait_for_load_state("networkidle")
    assert "Features" in page.title() or "features" in page.content().lower()


def test_create_feature_group_via_api(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test creating feature group via API
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {
        "name": group_name,
        "description": "test feature group",
        "entity": "user"
    }

    response = requests.post(
        f"{backend_url}/api/v1/features/groups",
        json=group_data,
        headers=auth_headers
    )
    assert response.status_code == 201, f"Create feature group failed: {response.text}"
    group = response.json()
    group_id = group["id"]

    db_group = db_utils.query_generic("feature_groups", group_id)
    assert db_group is not None
    assert db_group["name"] == group_name
    assert db_group["entity"] == "user"


def test_list_feature_groups_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing feature groups via API
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "host"}
    requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)

    response = requests.get(f"{backend_url}/api/v1/features/groups", headers=auth_headers)
    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)
    assert len(groups) > 0


def test_get_feature_group_by_id(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting feature group by id
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "user"}
    create_resp = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    group_id = create_resp.json()["id"]

    resp = requests.get(f"{backend_url}/api/v1/features/groups/{group_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == group_name


def test_get_feature_group_by_name(
    backend_url: str,
    auth_headers: dict
):
    '''
    test getting feature group by name
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "user"}
    requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)

    resp = requests.get(f"{backend_url}/api/v1/features/groups/name/{group_name}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == group_name


def test_add_feature_to_group(
    backend_url: str,
    db_utils: DBTestUtils,
    auth_headers: dict
):
    '''
    test adding a feature to a feature group
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "user"}
    create_resp = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    group_id = create_resp.json()["id"]

    feature_data = {
        "name": f"e2e_test_feat_{uuid4().hex[:8]}",
        "dtype": "float64",
        "transform": "zscore"
    }
    feat_resp = requests.post(
        f"{backend_url}/api/v1/features/groups/{group_id}/features",
        json=feature_data,
        headers=auth_headers
    )
    assert feat_resp.status_code == 201, f"Add feature failed: {feat_resp.text}"
    feature = feat_resp.json()
    assert feature["dtype"] == "float64"
    assert feature["transform"] == "zscore"

    db_feat = db_utils.query_generic("features", feature["id"])
    assert db_feat is not None


def test_list_features_in_group(
    backend_url: str,
    auth_headers: dict
):
    '''
    test listing features in a group
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "user"}
    create_resp = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    group_id = create_resp.json()["id"]

    # add two features
    for fname in ["login_count", "session_duration"]:
        feat_data = {"name": f"e2e_test_{fname}_{uuid4().hex[:8]}", "dtype": "float64"}
        requests.post(f"{backend_url}/api/v1/features/groups/{group_id}/features", json=feat_data, headers=auth_headers)

    feats_resp = requests.get(f"{backend_url}/api/v1/features/groups/{group_id}/features", headers=auth_headers)
    assert feats_resp.status_code == 200
    features = feats_resp.json()
    assert len(features) == 2


def test_duplicate_feature_group_name_rejected(
    backend_url: str,
    auth_headers: dict
):
    '''
    test that duplicate feature group names are rejected
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "test", "entity": "user"}
    resp1 = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    assert resp1.status_code == 201

    resp2 = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    assert resp2.status_code == 400


def test_delete_feature_group_via_api(
    backend_url: str,
    auth_headers: dict
):
    '''
    test deleting a feature group
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "to delete", "entity": "user"}
    create_resp = requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)
    group_id = create_resp.json()["id"]

    del_resp = requests.delete(f"{backend_url}/api/v1/features/groups/{group_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = requests.get(f"{backend_url}/api/v1/features/groups/{group_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_feature_group_appears_in_ui(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict
):
    '''
    test that feature group created via API appears in UI
    '''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    group_data = {"name": group_name, "description": "ui test", "entity": "user"}
    requests.post(f"{backend_url}/api/v1/features/groups", json=group_data, headers=auth_headers)

    page.goto(f"{frontend_url}/features")
    page.wait_for_load_state("networkidle")
    assert page.locator(f"text={group_name}").is_visible()
