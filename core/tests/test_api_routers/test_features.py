'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for features api router
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def _create_feature_group(test_client: TestClient, name: str = None) -> dict:
    '''helper to create a feature group and return the response data'''
    group_data = {
        "name": name or f"test-group-{uuid4().hex[:8]}",
        "description": "test feature group",
        "entity": "user",
    }
    response = test_client.post("/api/v1/features/groups", json=group_data)
    return response.json()


def test_create_feature_group(test_client: TestClient):
    '''
    test creating a feature group
    '''
    group_data = {
        "name": "login-features",
        "description": "user login behavior features",
        "entity": "user",
    }
    response = test_client.post("/api/v1/features/groups", json=group_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "login-features"
    assert data["description"] == "user login behavior features"
    assert data["entity"] == "user"
    assert "id" in data


def test_create_feature_group_default_entity(test_client: TestClient):
    '''
    test creating a feature group with default entity
    '''
    response = test_client.post("/api/v1/features/groups", json={
        "name": f"default-entity-group-{uuid4().hex[:8]}",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["entity"] == "default"


def test_create_feature_group_duplicate_name(test_client: TestClient):
    '''
    test creating a feature group with duplicate name returns 400
    '''
    name = f"duplicate-group-{uuid4().hex[:8]}"
    test_client.post("/api/v1/features/groups", json={"name": name})
    response = test_client.post("/api/v1/features/groups", json={"name": name})
    assert response.status_code == 400


def test_list_feature_groups(test_client: TestClient):
    '''
    test listing feature groups
    '''
    _create_feature_group(test_client)
    response = test_client.get("/api/v1/features/groups")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_feature_group(test_client: TestClient):
    '''
    test getting a feature group by id
    '''
    group = _create_feature_group(test_client, name=f"get-group-{uuid4().hex[:8]}")
    group_id = group["id"]
    response = test_client.get(f"/api/v1/features/groups/{group_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == group_id


def test_get_feature_group_not_found(test_client: TestClient):
    '''
    test getting a nonexistent feature group returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/features/groups/{fake_id}")
    assert response.status_code == 404


def test_get_feature_group_by_name(test_client: TestClient):
    '''
    test getting a feature group by name
    '''
    name = f"name-lookup-group-{uuid4().hex[:8]}"
    _create_feature_group(test_client, name=name)
    response = test_client.get(f"/api/v1/features/groups/name/{name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name


def test_get_feature_group_by_name_not_found(test_client: TestClient):
    '''
    test getting a nonexistent feature group by name returns 404
    '''
    response = test_client.get("/api/v1/features/groups/name/nonexistent-group")
    assert response.status_code == 404


def test_delete_feature_group(test_client: TestClient):
    '''
    test deleting a feature group
    '''
    group = _create_feature_group(test_client)
    group_id = group["id"]
    response = test_client.delete(f"/api/v1/features/groups/{group_id}")
    assert response.status_code == 204
    # verify deleted
    get_resp = test_client.get(f"/api/v1/features/groups/{group_id}")
    assert get_resp.status_code == 404


def test_delete_feature_group_not_found(test_client: TestClient):
    '''
    test deleting a nonexistent feature group returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.delete(f"/api/v1/features/groups/{fake_id}")
    assert response.status_code == 404


def test_add_feature(test_client: TestClient):
    '''
    test adding a feature to a feature group
    '''
    group = _create_feature_group(test_client)
    group_id = group["id"]
    feature_data = {
        "group_id": group_id,
        "name": "login_count",
        "dtype": "float64",
        "transform": "standard_scaler",
        "transform_params": {"with_mean": True, "with_std": True},
    }
    response = test_client.post(
        f"/api/v1/features/groups/{group_id}/features", json=feature_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "login_count"
    assert data["dtype"] == "float64"
    assert data["transform"] == "standard_scaler"
    assert data["group_id"] == group_id
    assert "id" in data


def test_add_feature_minimal(test_client: TestClient):
    '''
    test adding a feature with only required fields
    '''
    group = _create_feature_group(test_client)
    group_id = group["id"]
    feature_data = {
        "group_id": group_id,
        "name": "simple_feature",
    }
    response = test_client.post(
        f"/api/v1/features/groups/{group_id}/features", json=feature_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "simple_feature"


def test_add_feature_group_not_found(test_client: TestClient):
    '''
    test adding a feature to a nonexistent group returns 404
    '''
    fake_id = str(uuid4())
    feature_data = {
        "group_id": fake_id,
        "name": "orphan_feature",
    }
    response = test_client.post(
        f"/api/v1/features/groups/{fake_id}/features", json=feature_data
    )
    assert response.status_code == 404


def test_list_features(test_client: TestClient):
    '''
    test listing features in a feature group
    '''
    group = _create_feature_group(test_client)
    group_id = group["id"]
    # add multiple features
    for fname in ["feature_a", "feature_b", "feature_c"]:
        test_client.post(
            f"/api/v1/features/groups/{group_id}/features",
            json={"group_id": group_id, "name": fname}
        )
    response = test_client.get(f"/api/v1/features/groups/{group_id}/features")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_list_features_group_not_found(test_client: TestClient):
    '''
    test listing features for a nonexistent group returns 404
    '''
    fake_id = str(uuid4())
    response = test_client.get(f"/api/v1/features/groups/{fake_id}/features")
    assert response.status_code == 404
