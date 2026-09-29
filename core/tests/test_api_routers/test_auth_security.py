'''
Copyright 2019-Present The OpenUBA Platform Authors
security regression tests for JWT auth hardening (issue #149)

proves:
  (a) a token forged with the OLD committed literal secret is rejected
  (b) a token with role:admin but no user_id cannot reach admin routes
  (c) a well-formed token whose DB user-validation does not succeed
      (row missing OR the DB is unreachable) is rejected — fail closed
  (d) no token is rejected (fail closed)
  (e) a validated admin caller can still use the admin route
  (f) the config accessor is required (raises when unset / insecure / weak)

Note on the harness: the hardened get_current_user always validates the user via
get_db_context() (its own connection), which the testcontainer is not wired to.
So the REJECTION cases are exercised through the real decode/validate path (they
reject without needing a reachable DB), while the positive "admin can register"
case uses the established dependency-override pattern (see test_evaluation.py).
'''

import uuid

import pytest
from jose import jwt
from fastapi.testclient import TestClient

from core.fastapi_app import app
from core.auth import (
    create_access_token,
    get_current_user,
    ALGORITHM,
    SECRET_KEY,
    _INSECURE_SECRET,
    _load_secret_key,
    ConfigError,
)


def _register_payload() -> dict:
    return {
        "username": f"victim-{uuid.uuid4().hex[:8]}",
        "password": "hunter2-strong-password",
        "role": "analyst",
    }


# --- (a) token forged with the OLD literal secret is rejected ---

def test_token_signed_with_old_literal_secret_is_rejected(test_client: TestClient):
    # the running app is not signing with the insecure literal
    assert SECRET_KEY != _INSECURE_SECRET

    forged = jwt.encode(
        {"sub": "attacker", "user_id": str(uuid.uuid4()), "role": "admin"},
        _INSECURE_SECRET,
        algorithm=ALGORITHM,
    )
    resp = test_client.post(
        "/api/v1/auth/register",
        json=_register_payload(),
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code == 401, resp.text


# --- (b) role:admin but NO user_id cannot hit admin route (the #149 gap) ---

def test_admin_role_without_user_id_is_rejected(test_client: TestClient):
    forged = create_access_token({"sub": "attacker", "role": "admin"})  # no user_id
    resp = test_client.post(
        "/api/v1/auth/register",
        json=_register_payload(),
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code in (401, 403), resp.text


# --- (c) correct key + role:admin + a user_id whose DB validation does not
#         succeed (unknown row, or DB unreachable) is rejected — fail closed ---

def test_admin_role_with_invalid_user_id_is_rejected(test_client: TestClient):
    # a random user_id that will not validate against the DB; whether the users
    # row is simply absent or the DB is unreachable, get_current_user must reject
    # (only a literal "relation does not exist" during first-boot is allowed through).
    forged = create_access_token(
        {"sub": "attacker", "user_id": str(uuid.uuid4()), "role": "admin"}
    )
    resp = test_client.post(
        "/api/v1/auth/register",
        json=_register_payload(),
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code in (401, 403), resp.text


# --- (d) no token is rejected (fail closed) ---

def test_no_token_is_rejected(test_client: TestClient):
    resp = test_client.post("/api/v1/auth/register", json=_register_payload())
    assert resp.status_code in (401, 403), resp.text


# --- (e) a validated admin caller can still use the admin route ---

def test_validated_admin_can_register(test_client: TestClient):
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "admin",
        "user_id": str(uuid.uuid4()),
        "role": "admin",
        "payload": {},
    }
    try:
        resp = test_client.post("/api/v1/auth/register", json=_register_payload())
        assert resp.status_code == 201, resp.text
        assert resp.json()["role"] == "analyst"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# --- (f) the config accessor is required (fails closed) ---

def test_load_secret_key_raises_when_unset(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ConfigError):
        _load_secret_key()


def test_load_secret_key_rejects_insecure_literal(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", _INSECURE_SECRET)
    with pytest.raises(ConfigError):
        _load_secret_key()


def test_load_secret_key_rejects_short_key(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")
    with pytest.raises(ConfigError):
        _load_secret_key()


def test_load_secret_key_accepts_strong_key(monkeypatch):
    strong = "a" * 32
    monkeypatch.setenv("JWT_SECRET_KEY", strong)
    assert _load_secret_key() == strong
