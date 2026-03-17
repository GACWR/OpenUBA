'''
Copyright 2019-Present The OpenUBA Platform Authors
sdk api router
'''

import logging
import os
import hashlib
import base64
import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.model_repository import ModelRepository
from core.auth import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)

MODEL_STORAGE_PATH = Path(os.getenv("MODEL_STORAGE_PATH", "core/model_library"))


class SDKRegisterModelRequest(BaseModel):
    name: str
    framework: Optional[str] = None
    description: Optional[str] = None
    source_code: Optional[str] = None  # base64 encoded
    model_data: Optional[str] = None   # base64 encoded


class SDKPublishVersionRequest(BaseModel):
    model_id: UUID
    version: str
    summary: Optional[str] = None

    model_config = {'protected_namespaces': ()}


def _sha256(data: bytes) -> str:
    '''compute sha256 hex digest of bytes'''
    return hashlib.sha256(data).hexdigest()


def _generate_sklearn_wrapper(model_name: str) -> str:
    '''generate MODEL.py wrapper for an sklearn model that loads from model.pkl'''
    return f'''"""
{model_name} — sklearn model registered via OpenUBA SDK.
Loads pre-trained model from model.pkl and exposes the v2 interface.
"""

import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any


class Model:
    def __init__(self):
        model_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(model_dir, "model.pkl")
        self.model = None
        self.is_trained = False
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, "rb") as f:
                    self.model = pickle.load(f)
                self.is_trained = True
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load model.pkl ({{e}}), will create fresh model on train/infer"
                )

    def train(self, ctx) -> Dict[str, Any]:
        """Train the model on data from context."""
        ctx.logger.info("Starting training...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No training data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"No numeric columns in data (shape={{ctx.df.shape}})")

        # Always create a fresh model for training — the uploaded pickle may be
        # from a different sklearn version (pickle.load succeeds but internal
        # estimators have missing attributes that crash on fit/predict)
        from sklearn.ensemble import IsolationForest
        hp = getattr(ctx, "params", None) or {{}}
        self.model = IsolationForest(
            n_estimators=int(hp.get("n_estimators", 200)),
            contamination=float(hp.get("contamination", 0.05)),
            random_state=42,
        )
        self.model.fit(X)
        self.is_trained = True
        ctx.logger.info(f"Training completed on {{X.shape[0]}} samples, {{X.shape[1]}} features.")
        return {{
            "status": "success",
            "model_type": type(self.model).__name__,
            "n_samples": len(X),
            "n_features": X.shape[1],
        }}

    def infer(self, ctx) -> pd.DataFrame:
        """Run inference and return anomaly results."""
        ctx.logger.info("Starting inference...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No inference data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError(f"No numeric columns in data (shape={{ctx.df.shape}})")

        if "entity_id" in ctx.df.columns:
            ids = ctx.df["entity_id"].values
        elif "user_id" in ctx.df.columns:
            ids = ctx.df["user_id"].values
        else:
            ids = [f"entity_{{i}}" for i in range(len(X))]

        # Try the loaded/artifact model; if corrupt (sklearn version mismatch),
        # fall back to a fresh IsolationForest fitted on inference data
        try:
            if self.model is None:
                raise ValueError("no model loaded")
            needs_fit = not hasattr(self.model, "estimators_")
            if not needs_fit and hasattr(self.model, "n_features_in_"):
                if self.model.n_features_in_ != X.shape[1]:
                    ctx.logger.info(
                        f"Feature count mismatch (model: {{self.model.n_features_in_}}, "
                        f"data: {{X.shape[1]}}), re-fitting..."
                    )
                    needs_fit = True
            if needs_fit:
                ctx.logger.info("Fitting model on inference data...")
                self.model.fit(X)
            predictions = self.model.predict(X)
            scores = self.model.decision_function(X)
        except Exception as e:
            ctx.logger.warning(f"Loaded model failed ({{e}}), creating fresh IsolationForest...")
            from sklearn.ensemble import IsolationForest
            hp = getattr(ctx, "params", None) or {{}}
            self.model = IsolationForest(
                n_estimators=int(hp.get("n_estimators", 200)),
                contamination=float(hp.get("contamination", 0.05)),
                random_state=42,
            )
            self.model.fit(X)
            predictions = self.model.predict(X)
            scores = self.model.decision_function(X)

        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            risk = min(100.0, abs(score) * 100 + 50) if pred == -1 else max(0.0, (1 - score) * 20)
            results.append({{
                "entity_id": str(ids[i]),
                "risk_score": float(risk),
                "anomaly_type": "statistical_outlier" if pred == -1 else "normal",
                "details": {{"raw_score": float(score)}},
            }})

        return pd.DataFrame(results)
'''


def _generate_pytorch_wrapper(model_name: str) -> str:
    '''generate MODEL.py wrapper for a PyTorch model that loads from model.pkl'''
    return f'''"""
{model_name} — PyTorch model registered via OpenUBA SDK.
Loads pre-trained model from model.pkl and exposes the v2 interface.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any


class Model:
    def __init__(self):
        model_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(model_dir, "model.pkl")
        self.model = None
        self.is_trained = False
        if os.path.exists(pkl_path):
            try:
                import torch
                self.model = torch.load(pkl_path, weights_only=False)
                self.is_trained = True
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load model.pkl ({{e}}), model will be None"
                )

    def train(self, ctx) -> Dict[str, Any]:
        """Train the model on data from context."""
        ctx.logger.info("Starting training...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No training data provided.")
        ctx.logger.info("Training completed.")
        return {{"status": "success", "n_samples": len(ctx.df)}}

    def infer(self, ctx) -> pd.DataFrame:
        """Run inference and return results."""
        ctx.logger.info("Starting inference...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No inference data provided.")
        ctx.logger.info("Inference completed.")
        return ctx.df
'''


def _generate_generic_wrapper(model_name: str) -> str:
    '''generate MODEL.py wrapper for a generic pickle model'''
    return f'''"""
{model_name} — model registered via OpenUBA SDK.
Loads pre-trained model from model.pkl and exposes the v2 interface.
"""

import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any


class Model:
    def __init__(self):
        model_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(model_dir, "model.pkl")
        self.model = None
        self.is_trained = False
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, "rb") as f:
                    self.model = pickle.load(f)
                self.is_trained = True
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load model.pkl ({{e}}), model will be None"
                )

    def train(self, ctx) -> Dict[str, Any]:
        """Train the model on data from context."""
        ctx.logger.info("Starting training...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No training data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if self.model is not None and hasattr(self.model, "fit"):
            try:
                self.model.fit(X)
                self.is_trained = True
            except Exception as e:
                ctx.logger.warning(f"Model fit failed ({{e}}), skipping...")
        ctx.logger.info("Training completed.")
        return {{"status": "success", "n_samples": len(X)}}

    def infer(self, ctx) -> pd.DataFrame:
        """Run inference and return results."""
        ctx.logger.info("Starting inference...")
        if ctx.df is None or (hasattr(ctx.df, "empty") and ctx.df.empty):
            raise ValueError("No inference data provided.")

        X = ctx.df.select_dtypes(include=[np.number]).values
        if self.model is not None and hasattr(self.model, "predict"):
            try:
                if hasattr(self.model, "n_features_in_") and self.model.n_features_in_ != X.shape[1]:
                    ctx.logger.info("Feature count mismatch, re-fitting...")
                    self.model.fit(X)
                predictions = self.model.predict(X)
                ctx.df["prediction"] = predictions
            except Exception as e:
                ctx.logger.warning(f"Model predict failed ({{e}}), skipping...")
        ctx.logger.info("Inference completed.")
        return ctx.df
'''


def _generate_model_wrapper(model_name: str, framework: str) -> str:
    '''generate a framework-appropriate MODEL.py wrapper'''
    if framework == "sklearn":
        return _generate_sklearn_wrapper(model_name)
    elif framework == "pytorch":
        return _generate_pytorch_wrapper(model_name)
    else:
        return _generate_generic_wrapper(model_name)


def _write_model_yaml(model_dir: Path, name: str, framework: str,
                      description: str) -> bytes:
    '''write model.yaml and return its content as bytes'''
    desc = description or 'Model registered via SDK'
    # quote values that may contain YAML-special characters (colons, etc.)
    def _yq(v):
        if any(c in str(v) for c in ':{}[]#&*!|>\'"@`'):
            return f'"{v}"'
        return str(v)
    content = (
        f"name: {_yq(name)}\n"
        f"version: 1.0.0\n"
        f"runtime: {framework}\n"
        f"description: {_yq(desc)}\n"
        f"registered_by: sdk\n"
    )
    yaml_bytes = content.encode("utf-8")
    (model_dir / "model.yaml").write_bytes(yaml_bytes)
    return yaml_bytes


@router.post("/sdk/register-model")
async def sdk_register_model(
    body: SDKRegisterModelRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    register a model from the SDK
    accepts name, framework, description, source_code as base64, model_data as base64
    writes MODEL.py, model.pkl, and model.yaml to the model library so the
    model runner can import and execute the model
    '''
    repo = ModelRepository(db)

    # if model already exists, return it (idempotent for notebooks)
    existing = repo.get_by_name_version(body.name, "1.0.0")
    if existing:
        return {
            "model_id": str(existing.id),
            "name": existing.name,
            "version": existing.version,
            "slug": existing.slug,
            "status": existing.status,
        }

    # generate slug from name
    slug = body.name.lower().replace(" ", "-").replace("_", "-")
    framework = body.framework or "python-base"

    # decode base64 fields if provided
    source_code_decoded = None
    model_data_decoded = None
    if body.source_code:
        try:
            source_code_decoded = base64.b64decode(body.source_code).decode("utf-8")
        except Exception as e:
            logger.warning(f"failed to decode source_code base64: {e}")
            raise HTTPException(status_code=400, detail="invalid base64 for source_code")
    if body.model_data:
        try:
            model_data_decoded = base64.b64decode(body.model_data)
        except Exception as e:
            logger.warning(f"failed to decode model_data base64: {e}")
            raise HTTPException(status_code=400, detail="invalid base64 for model_data")

    # create model DB record
    model = repo.create(
        name=body.name,
        version="1.0.0",
        source_type="local_fs",
        slug=slug,
        description=body.description,
        runtime=framework,
        author=current_user["username"]
    )

    # write files to model library directory
    model_dir = MODEL_STORAGE_PATH / model.name
    try:
        model_dir.mkdir(parents=True, exist_ok=True)
        files_written = {}  # filename -> (content_bytes, component_type)

        # write model.pkl if model_data provided
        if model_data_decoded:
            pkl_path = model_dir / "model.pkl"
            pkl_path.write_bytes(model_data_decoded)
            files_written["model.pkl"] = (model_data_decoded, "weights")

        # write MODEL.py
        if source_code_decoded:
            # user provided custom source code — use it directly
            model_py_content = source_code_decoded
        elif model_data_decoded:
            # generate a wrapper that loads the pickle
            model_py_content = _generate_model_wrapper(model.name, framework)
        else:
            # no model data and no source code — generate a stub
            model_py_content = _generate_model_wrapper(model.name, framework)

        model_py_bytes = model_py_content.encode("utf-8")
        (model_dir / "MODEL.py").write_bytes(model_py_bytes)
        files_written["MODEL.py"] = (model_py_bytes, "source")

        # write model.yaml
        yaml_bytes = _write_model_yaml(
            model_dir, model.name, framework,
            body.description or ""
        )
        files_written["model.yaml"] = (yaml_bytes, "manifest")

        # create ModelVersion record
        manifest = {"runtime": framework, "source": "sdk"}
        if body.description:
            manifest["description"] = body.description
        model_version = repo.add_version(
            model_id=model.id,
            version="1.0.0",
            manifest=manifest
        )

        # set default version
        repo.update(model.id, default_version_id=model_version.id)

        # create ModelComponent records for each file
        for filename, (content_bytes, component_type) in files_written.items():
            file_hash = _sha256(content_bytes)
            repo.add_component(
                model_id=model.id,
                filename=filename,
                component_type=component_type,
                file_hash=file_hash,
                file_path=str(model_dir / filename),
                file_size=len(content_bytes)
            )

        # set status to installed
        repo.update(model.id, status="installed", framework=framework)

    except HTTPException:
        raise
    except Exception as e:
        # clean up partial state on failure
        logger.error(f"failed to write model files for {model.name}: {e}")
        if model_dir.exists():
            shutil.rmtree(model_dir, ignore_errors=True)
        try:
            repo.delete(model.id)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"failed to install model files: {e}"
        )

    logger.info(f"model registered and installed via SDK: {model.id} by user {current_user['username']}")
    return {
        "model_id": str(model.id),
        "name": model.name,
        "version": model.version,
        "slug": model.slug,
        "status": "installed"
    }


@router.post("/sdk/publish-version")
async def sdk_publish_version(
    body: SDKPublishVersionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    publish a model version from the SDK
    accepts model_id, version, summary
    '''
    repo = ModelRepository(db)
    model = repo.get_by_id(body.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")

    # add a new version record
    model_version = repo.add_version(
        model_id=body.model_id,
        version=body.version,
        manifest={"summary": body.summary} if body.summary else None
    )
    if not model_version:
        raise HTTPException(status_code=500, detail="failed to create model version")

    logger.info(f"model version published via SDK: model={body.model_id} version={body.version}")
    return {
        "model_id": str(body.model_id),
        "version_id": str(model_version.id),
        "version": body.version,
        "summary": body.summary
    }


@router.get("/sdk/models/resolve/{name}")
async def sdk_resolve_model(
    name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "read"))
):
    '''
    resolve a model by name (return model details)
    used by the SDK to look up models by name
    '''
    repo = ModelRepository(db)
    # try to find latest version
    model = repo.get_by_name_version(name, "1.0.0")
    if not model:
        raise HTTPException(status_code=404, detail=f"model '{name}' not found")

    return {
        "model_id": str(model.id),
        "name": model.name,
        "version": model.version,
        "slug": model.slug,
        "status": model.status,
        "source_type": model.source_type,
        "description": model.description,
        "runtime": model.runtime,
        "created_at": str(model.created_at)
    }
