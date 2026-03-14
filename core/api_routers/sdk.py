'''
Copyright 2019-Present The OpenUBA Platform Authors
sdk api router
'''

import logging
import base64
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.model_repository import ModelRepository
from core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.post("/sdk/register-model")
async def sdk_register_model(
    body: SDKRegisterModelRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    '''
    register a model from the SDK
    accepts name, framework, description, source_code as base64, model_data as base64
    '''
    repo = ModelRepository(db)

    # check if model already exists
    existing = repo.get_by_name_version(body.name, "1.0.0")
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"model '{body.name}' version 1.0.0 already exists"
        )

    # generate slug from name
    slug = body.name.lower().replace(" ", "-").replace("_", "-")

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

    model = repo.create(
        name=body.name,
        version="1.0.0",
        source_type="local_fs",
        slug=slug,
        description=body.description,
        runtime=body.framework or "python-base"
    )

    # store source code as a component if provided
    if source_code_decoded:
        import hashlib
        file_hash = hashlib.sha256(source_code_decoded.encode("utf-8")).hexdigest()
        repo.add_component(
            model_id=model.id,
            filename="MODEL.py",
            component_type="source",
            file_hash=file_hash,
            file_size=len(source_code_decoded)
        )

    logger.info(f"model registered via SDK: {model.id} by user {current_user['username']}")
    return {
        "model_id": str(model.id),
        "name": model.name,
        "version": model.version,
        "slug": model.slug,
        "status": model.status
    }


@router.post("/sdk/publish-version")
async def sdk_publish_version(
    body: SDKPublishVersionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
