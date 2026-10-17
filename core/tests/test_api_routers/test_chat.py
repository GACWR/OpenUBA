'''
Copyright 2019-Present The OpenUBA Platform Authors
chat api router tests — auth coverage (close unauthenticated LLM-proxy gap)
'''

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from core.fastapi_app import app
from core.auth import get_current_user
from core.db.connection import get_db


@pytest.fixture(autouse=True)
def _as_admin():
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


def test_chat_requires_authentication(unauthenticated_client: TestClient):
    '''
    POST /chat proxies a billable LLM provider and accepts page context — it
    must reject unauthenticated callers (401 before the stream starts).
    '''
    resp = unauthenticated_client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert resp.status_code == 401
