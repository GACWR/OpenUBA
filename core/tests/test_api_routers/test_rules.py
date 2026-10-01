'''
Copyright 2019-Present The OpenUBA Platform Authors
rules api router tests
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from core.fastapi_app import app
from core.auth import get_current_user
from core.db.connection import get_db


@pytest.fixture(autouse=True)
def _as_admin():
    '''authenticate every request in this module as an admin (bypasses require_permission)'''
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "admin", "user_id": str(uuid4()), "role": "admin", "payload": {},
    }
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def unauthenticated_client(_as_admin):
    '''client with NO auth override → protected routes must 401'''
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = lambda: object()
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)


def test_create_rule(test_client: TestClient):
    '''
    test creating a rule
    '''
    rule_data = {
        "name": "test rule",
        "description": "test rule description",
        "rule_type": "single-fire",
        "condition": "risk_score > 80",
        "features": ["feature1", "feature2"],
        "score": 10.0,
        "enabled": True
    }
    response = test_client.post("/api/v1/rules", json=rule_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test rule"
    assert data["rule_type"] == "single-fire"
    assert "id" in data


def test_list_rules(test_client: TestClient):
    '''
    test listing rules
    '''
    # create a rule first
    rule_data = {
        "name": "list test rule",
        "description": "test",
        "rule_type": "deviation",
        "condition": "value > threshold",
        "features": [],
        "score": 5.0,
        "enabled": True
    }
    test_client.post("/api/v1/rules", json=rule_data)
    
    # list rules
    response = test_client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_rule(test_client: TestClient):
    '''
    test getting a rule by id
    '''
    # create a rule
    rule_data = {
        "name": "get test rule",
        "description": "test",
        "rule_type": "single-fire",
        "condition": "test > 0",
        "features": [],
        "score": 1.0,
        "enabled": True
    }
    create_response = test_client.post("/api/v1/rules", json=rule_data)
    rule_id = create_response.json()["id"]
    
    # get the rule
    response = test_client.get(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule_id
    assert data["name"] == "get test rule"


def test_create_alert(test_client: TestClient):
    '''
    raise an alert directly via the api (the OpenUBA SDK path). with no
    rule_id, create_alert get-or-creates the synthetic SDK rule.
    '''
    payload = {
        "severity": "high",
        "message": "suspicious login burst",
        "entity_id": "user42",
        "entity_type": "user",
        "notify": False,
    }
    response = test_client.post("/api/v1/alerts", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["severity"] == "high"
    assert "id" in data


def test_create_alert_with_unknown_rule_id_is_404(test_client: TestClient):
    '''an explicit but non-existent rule_id must 404, not silently create'''
    payload = {"message": "x", "severity": "low", "rule_id": str(uuid4())}
    response = test_client.post("/api/v1/alerts", json=payload)
    assert response.status_code == 404


def test_create_alert_requires_authentication(unauthenticated_client: TestClient):
    '''POST /alerts must reject unauthenticated callers (401 before any DB).'''
    resp = unauthenticated_client.post(
        "/api/v1/alerts", json={"message": "unauth", "severity": "low"}
    )
    assert resp.status_code == 401


def _patch_permission_db(monkeypatch, db_session):
    '''route require_permission's own get_db_context at the testcontainer so a
    real (role, page) permission lookup is exercised (admin bypasses it, so the
    page gate can only be proven with a non-admin role + seeded rows).'''
    from contextlib import contextmanager
    import core.db as core_db

    @contextmanager
    def _ctx():
        yield db_session

    monkeypatch.setattr(core_db, "get_db_context", _ctx)


def test_create_alert_is_gated_on_alerts_write_not_anomalies_write(
    test_client: TestClient, db_session, monkeypatch
):
    '''
    the headline #144 change: POST /alerts is gated on alerts:write, NOT
    anomalies:write. prove it DISCRIMINATES — an analyst that HAS anomalies:write
    but LACKS alerts:write must be denied (403). if the guard were still
    anomalies:write this would wrongly return 201.
    '''
    from core.db.models import RolePermission
    db_session.add(RolePermission(role="analyst", page="anomalies", can_read=True, can_write=True))
    db_session.add(RolePermission(role="analyst", page="alerts", can_read=True, can_write=False))
    db_session.flush()
    _patch_permission_db(monkeypatch, db_session)

    app.dependency_overrides[get_current_user] = lambda: {
        "username": "ana", "user_id": str(uuid4()), "role": "analyst", "payload": {},
    }
    try:
        resp = test_client.post("/api/v1/alerts", json={"message": "x", "severity": "low"})
        assert resp.status_code == 403, resp.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_create_alert_allowed_with_alerts_write(
    test_client: TestClient, db_session, monkeypatch
):
    '''a non-admin role explicitly granted alerts:write CAN create an alert.'''
    from core.db.models import RolePermission
    db_session.add(RolePermission(role="analyst", page="alerts", can_read=True, can_write=True))
    db_session.flush()
    _patch_permission_db(monkeypatch, db_session)

    app.dependency_overrides[get_current_user] = lambda: {
        "username": "ana", "user_id": str(uuid4()), "role": "analyst", "payload": {},
    }
    try:
        resp = test_client.post("/api/v1/alerts", json={"message": "ok", "severity": "low"})
        assert resp.status_code == 201, resp.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)

