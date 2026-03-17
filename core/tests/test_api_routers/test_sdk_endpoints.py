'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for sdk api router endpoints
'''

import pytest
import base64
import pickle
import os
import yaml
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from core.auth import get_current_user
from core.fastapi_app import app
import core.api_routers.sdk as sdk_module


MOCK_ADMIN_USER = {
    "username": "test-admin",
    "user_id": str(uuid4()),
    "role": "admin",
    "payload": {},
}

MOCK_READONLY_USER = {
    "username": "test-readonly",
    "user_id": str(uuid4()),
    "role": "triage",
    "payload": {},
}


@pytest.fixture(autouse=True)
def _auth_override():
    '''override auth to return a mock admin user for all tests in this module'''
    async def mock_get_current_user():
        return MOCK_ADMIN_USER

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture()
def model_storage(tmp_path, monkeypatch):
    '''redirect MODEL_STORAGE_PATH to a temp directory so tests don't write to core/model_library'''
    monkeypatch.setattr(sdk_module, "MODEL_STORAGE_PATH", tmp_path)
    return tmp_path


def _make_sklearn_model_data() -> str:
    '''create a real sklearn IsolationForest, pickle it, and return base64'''
    from sklearn.ensemble import IsolationForest
    import numpy as np

    clf = IsolationForest(contamination=0.1, random_state=42, n_estimators=10)
    rng = np.random.RandomState(42)
    X = rng.randn(50, 3)
    clf.fit(X)

    import io
    buf = io.BytesIO()
    pickle.dump(clf, buf)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _register_model_via_sdk(test_client: TestClient, name: str = None,
                            framework: str = "sklearn", model_data: str = None,
                            source_code: str = None) -> dict:
    '''helper to register a model via SDK endpoint and return the response data'''
    body = {
        "name": name or f"sdk-model-{uuid4().hex[:8]}",
        "framework": framework,
        "description": "model registered via SDK",
    }
    if model_data:
        body["model_data"] = model_data
    if source_code:
        body["source_code"] = source_code
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    return response


# ─── Basic Registration Tests ────────────────────────────────────────


def test_sdk_register_model(test_client: TestClient, model_storage):
    '''test registering a model via SDK endpoint creates installed model'''
    body = {
        "name": "sdk-test-model",
        "framework": "sklearn",
        "description": "test model from SDK",
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "sdk-test-model"
    assert data["version"] == "1.0.0"
    assert data["slug"] == "sdk-test-model"
    assert data["status"] == "installed"
    assert "model_id" in data


def test_sdk_register_model_duplicate(test_client: TestClient, model_storage):
    '''test registering a model with duplicate name returns existing model (idempotent)'''
    name = f"sdk-dup-model-{uuid4().hex[:8]}"
    first = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
    })
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
    })
    assert response.status_code == 200
    assert response.json()["model_id"] == first.json()["model_id"]


def test_sdk_register_model_invalid_base64(test_client: TestClient, model_storage):
    '''test registering a model with invalid base64 returns 400'''
    body = {
        "name": f"sdk-bad-b64-{uuid4().hex[:8]}",
        "framework": "sklearn",
        "source_code": "not-valid-base64!!!",
    }
    response = test_client.post("/api/v1/sdk/register-model", json=body)
    assert response.status_code == 400


# ─── Model Data (Pickle) Tests ──────────────────────────────────────


def test_sdk_register_model_with_model_data(test_client: TestClient, model_storage, db_session):
    '''test that registering with model_data writes pickle, MODEL.py, and model.yaml to disk'''
    model_data = _make_sklearn_model_data()
    name = f"sdk-pkl-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
        "description": "sklearn model with pickle",
        "model_data": model_data,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "installed"

    # verify files on disk
    model_dir = model_storage / name
    assert model_dir.exists()
    assert (model_dir / "MODEL.py").exists()
    assert (model_dir / "model.pkl").exists()
    assert (model_dir / "model.yaml").exists()

    # verify model.pkl is a valid pickle
    with open(model_dir / "model.pkl", "rb") as f:
        loaded_model = pickle.load(f)
    assert hasattr(loaded_model, "predict")
    assert hasattr(loaded_model, "decision_function")

    # verify MODEL.py contains the v2 interface
    model_py_content = (model_dir / "MODEL.py").read_text()
    assert "class Model:" in model_py_content
    assert "def train(self, ctx)" in model_py_content
    assert "def infer(self, ctx)" in model_py_content
    assert "model.pkl" in model_py_content

    # verify model.yaml
    with open(model_dir / "model.yaml") as f:
        yaml_data = yaml.safe_load(f)
    assert yaml_data["name"] == name
    assert yaml_data["runtime"] == "sklearn"
    assert yaml_data["version"] == "1.0.0"
    assert yaml_data["registered_by"] == "sdk"

    # verify DB records: ModelVersion exists
    from core.db.models import Model, ModelVersion, ModelComponent
    model_record = db_session.query(Model).filter(Model.name == name).first()
    assert model_record is not None
    assert model_record.status == "installed"
    assert model_record.author == MOCK_ADMIN_USER["username"]
    assert model_record.default_version_id is not None

    versions = db_session.query(ModelVersion).filter(
        ModelVersion.model_id == model_record.id
    ).all()
    assert len(versions) == 1
    assert versions[0].version == "1.0.0"

    # verify ModelComponent records (MODEL.py, model.pkl, model.yaml)
    components = db_session.query(ModelComponent).filter(
        ModelComponent.model_id == model_record.id
    ).all()
    component_filenames = {c.filename for c in components}
    assert "MODEL.py" in component_filenames
    assert "model.pkl" in component_filenames
    assert "model.yaml" in component_filenames
    assert len(components) == 3

    # verify component types
    comp_map = {c.filename: c for c in components}
    assert comp_map["MODEL.py"].component_type == "source"
    assert comp_map["model.pkl"].component_type == "weights"
    assert comp_map["model.yaml"].component_type == "manifest"

    # verify file hashes are non-empty
    for comp in components:
        assert comp.file_hash is not None
        assert len(comp.file_hash) == 64  # sha256 hex


# ─── Source Code Tests ───────────────────────────────────────────────


def test_sdk_register_model_with_source_code(test_client: TestClient, model_storage):
    '''test registering with custom source code writes it as MODEL.py'''
    source_code = "class Model:\n    def train(self, ctx):\n        pass\n    def infer(self, ctx):\n        return ctx.df\n"
    encoded = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
    name = f"sdk-code-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
        "description": "model with source code",
        "source_code": encoded,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "installed"

    # verify MODEL.py on disk matches decoded source
    model_dir = model_storage / name
    assert (model_dir / "MODEL.py").exists()
    written_content = (model_dir / "MODEL.py").read_text()
    assert written_content == source_code

    # verify model.yaml also written
    assert (model_dir / "model.yaml").exists()

    # no model.pkl since we didn't provide model_data
    assert not (model_dir / "model.pkl").exists()


def test_sdk_register_model_with_both_source_and_data(test_client: TestClient, model_storage):
    '''test that source_code takes precedence for MODEL.py when both are provided'''
    model_data = _make_sklearn_model_data()
    source_code = "class Model:\n    def train(self, ctx):\n        return {'custom': True}\n"
    encoded_source = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
    name = f"sdk-both-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
        "model_data": model_data,
        "source_code": encoded_source,
    })
    assert response.status_code == 200

    model_dir = model_storage / name
    # source_code should be used for MODEL.py
    written_content = (model_dir / "MODEL.py").read_text()
    assert written_content == source_code
    assert "custom" in written_content

    # model.pkl should also be saved
    assert (model_dir / "model.pkl").exists()


# ─── ModelVersion and Default Version Tests ──────────────────────────


def test_sdk_register_model_creates_version(test_client: TestClient, model_storage, db_session):
    '''test that registration creates a ModelVersion record with correct manifest'''
    name = f"sdk-ver-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
        "description": "versioned model",
    })
    assert response.status_code == 200

    from core.db.models import Model, ModelVersion
    model_record = db_session.query(Model).filter(Model.name == name).first()
    assert model_record is not None

    version = db_session.query(ModelVersion).filter(
        ModelVersion.model_id == model_record.id,
        ModelVersion.version == "1.0.0"
    ).first()
    assert version is not None
    assert version.manifest is not None
    assert version.manifest.get("runtime") == "sklearn"
    assert version.manifest.get("source") == "sdk"


def test_sdk_register_model_sets_default_version(test_client: TestClient, model_storage, db_session):
    '''test that registration sets the default_version_id on the model'''
    name = f"sdk-defver-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
    })
    assert response.status_code == 200

    from core.db.models import Model, ModelVersion
    model_record = db_session.query(Model).filter(Model.name == name).first()
    assert model_record is not None
    assert model_record.default_version_id is not None

    version = db_session.query(ModelVersion).filter(
        ModelVersion.id == model_record.default_version_id
    ).first()
    assert version is not None
    assert version.version == "1.0.0"


# ─── Generated MODEL.py Importability Test ───────────────────────────


def test_sdk_register_model_generated_wrapper_is_importable(test_client: TestClient, model_storage):
    '''test that the generated MODEL.py can be imported by the model runner'''
    import importlib.util
    import sys

    model_data = _make_sklearn_model_data()
    name = f"sdk-import-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "sklearn",
        "model_data": model_data,
    })
    assert response.status_code == 200

    model_dir = model_storage / name
    model_py = model_dir / "MODEL.py"
    assert model_py.exists()

    # import the generated MODULE.py just like the model runner does
    spec = importlib.util.spec_from_file_location("MODEL", str(model_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # verify v2 interface
    assert hasattr(mod, "Model")
    instance = mod.Model()
    assert hasattr(instance, "train")
    assert hasattr(instance, "infer")
    assert instance.is_trained is True  # loaded from pickle
    assert instance.model is not None


# ─── Permission Tests ────────────────────────────────────────────────


def test_sdk_register_model_requires_write_permission(test_client: TestClient, model_storage):
    '''test that register-model enforces models write permission'''
    # override auth to return a non-admin user with no write permission
    async def mock_triage_user():
        return MOCK_READONLY_USER

    app.dependency_overrides[get_current_user] = mock_triage_user
    try:
        body = {
            "name": f"sdk-perm-model-{uuid4().hex[:8]}",
            "framework": "sklearn",
        }
        response = test_client.post("/api/v1/sdk/register-model", json=body)
        # should get 403 (triage role has no write to models)
        # or 401 if the permission check fails
        assert response.status_code in (401, 403)
    finally:
        # restore admin override
        async def mock_admin():
            return MOCK_ADMIN_USER
        app.dependency_overrides[get_current_user] = mock_admin


# ─── Publish Version Tests ───────────────────────────────────────────


def test_sdk_publish_version(test_client: TestClient, model_storage):
    '''test publishing a model version via SDK endpoint'''
    resp = _register_model_via_sdk(test_client)
    assert resp.status_code == 200
    model = resp.json()
    model_id = model["model_id"]
    body = {
        "model_id": model_id,
        "version": "2.0.0",
        "summary": "improved accuracy",
    }
    response = test_client.post("/api/v1/sdk/publish-version", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == model_id
    assert data["version"] == "2.0.0"
    assert data["summary"] == "improved accuracy"
    assert "version_id" in data


def test_sdk_publish_version_model_not_found(test_client: TestClient, model_storage):
    '''test publishing a version for nonexistent model returns 404'''
    fake_id = str(uuid4())
    body = {
        "model_id": fake_id,
        "version": "2.0.0",
    }
    response = test_client.post("/api/v1/sdk/publish-version", json=body)
    assert response.status_code == 404


# ─── Resolve Model Tests ────────────────────────────────────────────


def test_sdk_resolve_model(test_client: TestClient, model_storage):
    '''test resolving a model by name'''
    name = f"sdk-resolve-model-{uuid4().hex[:8]}"
    _register_model_via_sdk(test_client, name=name)
    response = test_client.get(f"/api/v1/sdk/models/resolve/{name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["version"] == "1.0.0"
    assert data["status"] == "installed"
    assert "model_id" in data
    assert "slug" in data
    assert "source_type" in data


def test_sdk_resolve_model_not_found(test_client: TestClient):
    '''test resolving a nonexistent model returns 404'''
    response = test_client.get("/api/v1/sdk/models/resolve/nonexistent-model")
    assert response.status_code == 404


# ─── Framework-Specific Wrapper Tests ────────────────────────────────


def test_sdk_register_pytorch_model_generates_pytorch_wrapper(test_client: TestClient, model_storage):
    '''test that pytorch framework generates pytorch-specific wrapper'''
    name = f"sdk-pytorch-model-{uuid4().hex[:8]}"
    # just register with framework=pytorch, no actual model_data (stub wrapper)
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "pytorch",
    })
    assert response.status_code == 200

    model_dir = model_storage / name
    content = (model_dir / "MODEL.py").read_text()
    assert "torch.load" in content
    assert "class Model:" in content


def test_sdk_register_generic_model_generates_generic_wrapper(test_client: TestClient, model_storage):
    '''test that unknown framework generates generic pickle wrapper'''
    name = f"sdk-generic-model-{uuid4().hex[:8]}"
    response = test_client.post("/api/v1/sdk/register-model", json={
        "name": name,
        "framework": "python-base",
    })
    assert response.status_code == 200

    model_dir = model_storage / name
    content = (model_dir / "MODEL.py").read_text()
    assert "pickle.load" in content
    assert "class Model:" in content
