'''
Copyright 2019-Present The OpenUBA Platform Authors
models api router
'''

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_db
from core.repositories.model_repository import ModelRepository
from core.repositories.job_repository import JobRepository
from core.api_schemas.models import ModelCreate, ModelUpdate, ModelResponse
from core.auth import require_permission, get_current_user


class TrainRequest(BaseModel):
    data_source: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    source_group_slug: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    version_id: Optional[str] = None


class ExecuteRequest(BaseModel):
    data_source: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    source_group_slug: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    version_id: Optional[str] = None
    artifact_id: Optional[str] = None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    register a new model
    '''
    repo = ModelRepository(db)
    # check if model already exists
    existing = repo.get_by_name_version(model_data.name, model_data.version)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"model {model_data.name} version {model_data.version} already exists"
        )
    # generate slug from name
    slug = model_data.name.lower().replace(" ", "-").replace("_", "-")
    
    model = repo.create(
        name=model_data.name,
        version=model_data.version,
        source_type=model_data.source_type,
        slug=slug,
        source_url=model_data.source_url,
        manifest=model_data.manifest,
        description=model_data.description,
        author=model_data.author,
        enabled=model_data.enabled,
        runtime=model_data.runtime
    )
    return model


@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    status: Optional[str] = Query(None, pattern="^(pending|installed|active|disabled)$"),
    source_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    '''
    list installed models with optional filters
    '''
    from core.services.model_installer import ModelInstaller
    
    # sync local models
    try:
        installer = ModelInstaller()
        installer.discover_local_models()
    except Exception as e:
        logger.warning(f"failed to discover local models: {e}")

    repo = ModelRepository(db)
    models = repo.list_all(
        status=status,
        source_type=source_type,
        enabled=enabled,
        limit=limit,
        offset=offset
    )
    return models


@router.get("/models/search")
async def search_models(
    query: Optional[str] = Query(None, description="search query"),
    source_type: Optional[str] = Query(None, description="filter by source type"),
    registry_type: str = Query("all", description="search 'code', 'weights', or 'all' registries"),
    db: Session = Depends(get_db)
):
    '''
    unified search for models across all registries
    searches both code and weights registries by default
    deduplicates results by name and annotates with install status
    '''
    from core.registry import RegistryService

    try:
        registry_service = RegistryService()

        # convert source_type to list if provided
        source_types = [source_type] if source_type else None

        # use unified search method
        results = registry_service.search_models(
            query=query or "",
            source_types=source_types,
            registry_type=registry_type
        )

        # deduplicate by model name, prefer hub source for richer metadata
        seen = {}
        for result in results:
            name = result.get("name")
            if not name:
                continue
            existing = seen.get(name)
            if not existing:
                seen[name] = result
            elif result.get("source_type") == "openuba_hub" and existing.get("source_type") != "openuba_hub":
                seen[name] = result

        deduped = list(seen.values())

        # annotate with install status from DB
        repo = ModelRepository(db)
        for result in deduped:
            name = result.get("name")
            version = result.get("version", "1.0.0")
            existing = repo.get_by_name_version(name, version) if name else None
            result["installed"] = existing is not None
            result["installed_model_id"] = str(existing.id) if existing else None

        return {
            "models": deduped,
            "total": len(deduped),
            "query": query,
            "source_type": source_type,
            "registry_type": registry_type
        }
    except Exception as e:
        logger.error(f"model search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    db: Session = Depends(get_db)
):
    '''
    get model by id
    '''
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    return model


@router.post("/models/{model_id}/install", response_model=ModelResponse)
async def install_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    install a model (pull down code, verify checksums, mark as ready)
    uses model installer service to download and verify model files
    '''
    from core.services.model_installer import ModelInstaller
    
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    if model.status == "installed":
        raise HTTPException(status_code=400, detail="model already installed")
    
    try:
        # use model installer to download and install
        installer = ModelInstaller()
        # if model has source_url or source_type, try to install from registry
        if model.source_url or model.source_type:
            installed_model_id = installer.install_model(
                code_source_type=model.source_type,
                model_id=model.name,
                model_name=model.name,
                model_version=model.version
            )
            logger.info(f"model {model_id} installed via installer service")
        else:
            # just mark as installed if no source info
            model = repo.update(model_id, status="installed")
            logger.info(f"model {model_id} marked as installed (no source info)")
        
        # refresh model from db
        model = repo.get_by_id(model_id)
        return model
    except Exception as e:
        logger.error(f"model installation failed: {e}")
        raise HTTPException(status_code=500, detail=f"model installation failed: {str(e)}")






@router.get("/models/{model_id}/code")
async def get_model_code(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "read"))
):
    '''
    get model source code content
    '''
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
        
    # verify component exists
    components = repo.get_components(model_id)
    target_filename = None
    
    # helper to find best matching code file
    for c in components:
        if c.filename in ["MODEL.py", "model.py", "main.py"]:
            target_filename = c.filename
            break
            
    if not target_filename:
        # fallback: find first python file
        for c in components:
            if c.filename.endswith(".py"):
                target_filename = c.filename
                break
                
    if not target_filename:
        # fallback: try MODEL.py even if not in components (legacy import support)
        target_filename = "MODEL.py"

    # construct path
    storage_path = Path(os.getenv("MODEL_STORAGE_PATH", "core/model_library"))
    model_path = storage_path / model.name
    file_path = model_path / target_filename
    
    if not file_path.exists():
         # Last ditch: try slug
         model_path_slug = storage_path / model.slug
         file_path_slug = model_path_slug / target_filename
         if file_path_slug.exists():
             file_path = file_path_slug
         else:
             raise HTTPException(status_code=404, detail=f"source file {target_filename} not found")

    try:
        with open(file_path, "r") as f:
            content = f.read()
        return {
            "model_id": str(model_id),
            "filename": target_filename,
            "language": "python",
            "content": content
        }
    except Exception as e:
        logger.error(f"failed to read code file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/train")
async def train_model(
    model_id: UUID,
    body: Optional[TrainRequest] = Body(None),
    version_id: Optional[UUID] = Query(None, description="model version id (uses default if not specified)"),
    data_source: Optional[str] = Query(None, description="data source: 'spark', 'elasticsearch', or 'local_csv'"),
    table_name: Optional[str] = Query(None, description="spark table name"),
    index_name: Optional[str] = Query(None, description="elasticsearch index name"),
    file_path: Optional[str] = Query(None, description="local file path"),
    file_name: Optional[str] = Query(None, description="local file name"),
    source_group_slug: Optional[str] = Query(None, description="source group slug"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    train a model on data
    this will enqueue a training job to the model execution sandbox
    supports selecting data source via JSON body or query params
    '''
    from core.services.model_orchestrator import ModelOrchestrator

    # merge body and query params (body takes precedence)
    _data_source = (body.data_source if body else None) or data_source
    _table_name = (body.table_name if body else None) or table_name
    _index_name = (body.index_name if body else None) or index_name
    _file_path = (body.file_path if body else None) or file_path
    _file_name = (body.file_name if body else None) or file_name
    _source_group_slug = (body.source_group_slug if body else None) or source_group_slug
    _query = (body.query if body else None) or {"match_all": {}}
    _version_id = None
    if body and body.version_id:
        _version_id = UUID(body.version_id)
    elif version_id:
        _version_id = version_id

    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    if model.status != "installed" and model.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"model must be installed or active to train, current status: {model.status}"
        )

    # prepare input data for model
    input_data = {}
    if _data_source:
        input_data["data_source"] = _data_source
        input_data["type"] = _data_source
        if _data_source == "spark" and _table_name:
            input_data["table_name"] = _table_name
        elif _data_source == "elasticsearch":
            if _index_name:
                input_data["index_name"] = _index_name
                input_data["index"] = _index_name
            input_data["query"] = _query
        elif _data_source == "local_csv" and _file_path and _file_name:
            input_data["file_path"] = _file_path
            input_data["file_name"] = _file_name
        elif _data_source == "source_group" and _source_group_slug:
            input_data["source_group_slug"] = _source_group_slug

    try:
        orchestrator = ModelOrchestrator()
        run_id = orchestrator.execute_model_background(
            model_id,
            input_data=input_data if input_data else None,
            run_type="train",
            version_id=_version_id
        )
        logger.info(f"model training dispatched: run_id={run_id} for model {model_id}")

        # create a Job record so this shows up in the /jobs page
        try:
            job_repo = JobRepository(db)
            job_repo.create(
                model_id=model_id,
                job_type="training",
                created_by=UUID(current_user["user_id"]),
                hardware_tier="cpu-small",
                model_run_id=run_id,
            )
        except Exception as je:
            logger.warning(f"failed to create job record for training: {je}")

        return {
            "model_id": str(model_id),
            "run_id": str(run_id),
            "status": "dispatched",
            "message": "model training dispatched",
            "input_data": input_data if input_data else None
        }
    except Exception as e:
        logger.error(f"model training failed: {e}")
        raise HTTPException(status_code=500, detail=f"model training failed: {str(e)}")


@router.post("/models/{model_id}/execute")
async def execute_model(
    model_id: UUID,
    body: Optional[ExecuteRequest] = Body(None),
    version_id: Optional[UUID] = Query(None, description="model version id (uses default if not specified)"),
    artifact_id: Optional[UUID] = Query(None, description="artifact id (uses latest checkpoint if not specified)"),
    data_source: Optional[str] = Query(None, description="data source: 'spark', 'elasticsearch', or 'local_csv'"),
    table_name: Optional[str] = Query(None, description="spark table name"),
    index_name: Optional[str] = Query(None, description="elasticsearch index name"),
    file_path: Optional[str] = Query(None, description="local file path"),
    file_name: Optional[str] = Query(None, description="local file name"),
    source_group_slug: Optional[str] = Query(None, description="source group slug"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    trigger a model execution (inference) on latest data
    this will enqueue a job to the model execution sandbox
    supports selecting data source via JSON body or query params
    '''
    from core.services.model_orchestrator import ModelOrchestrator

    # merge body and query params (body takes precedence)
    _data_source = (body.data_source if body else None) or data_source
    _table_name = (body.table_name if body else None) or table_name
    _index_name = (body.index_name if body else None) or index_name
    _file_path = (body.file_path if body else None) or file_path
    _file_name = (body.file_name if body else None) or file_name
    _source_group_slug = (body.source_group_slug if body else None) or source_group_slug
    _query = (body.query if body else None) or {"match_all": {}}
    _version_id = None
    if body and body.version_id:
        _version_id = UUID(body.version_id)
    elif version_id:
        _version_id = version_id
    _artifact_id = None
    if body and body.artifact_id:
        _artifact_id = UUID(body.artifact_id)
    elif artifact_id:
        _artifact_id = artifact_id

    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    if model.status != "installed" and model.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"model must be installed or active to execute, current status: {model.status}"
        )

    # prepare input data for model
    input_data = {}
    if _data_source:
        input_data["data_source"] = _data_source
        input_data["type"] = _data_source
        if _data_source == "spark" and _table_name:
            input_data["table_name"] = _table_name
        elif _data_source == "elasticsearch":
            if _index_name:
                input_data["index_name"] = _index_name
                input_data["index"] = _index_name
            input_data["query"] = _query
        elif _data_source == "local_csv" and _file_path and _file_name:
            input_data["file_path"] = _file_path
            input_data["file_name"] = _file_name
        elif _data_source == "source_group" and _source_group_slug:
            input_data["source_group_slug"] = _source_group_slug

    try:
        orchestrator = ModelOrchestrator()
        run_id = orchestrator.execute_model_background(
            model_id,
            input_data=input_data if input_data else None,
            run_type="infer",
            version_id=_version_id,
            artifact_id=_artifact_id
        )
        logger.info(f"model execution dispatched: run_id={run_id} for model {model_id}")

        # create a Job record so this shows up in the /jobs page
        try:
            job_repo = JobRepository(db)
            job_repo.create(
                model_id=model_id,
                job_type="inference",
                created_by=UUID(current_user["user_id"]),
                hardware_tier="cpu-small",
                model_run_id=run_id,
            )
        except Exception as je:
            logger.warning(f"failed to create job record for inference: {je}")

        return {
            "model_id": str(model_id),
            "run_id": str(run_id),
            "status": "dispatched",
            "message": "model execution dispatched",
            "input_data": input_data if input_data else None
        }
    except Exception as e:
        logger.error(f"model execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"model execution failed: {str(e)}")


@router.patch("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: UUID,
    model_data: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    update model fields
    '''
    repo = ModelRepository(db)
    model = repo.update(model_id, **model_data.dict(exclude_unset=True))
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    return model


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("models", "write"))
):
    '''
    delete a model
    '''
    repo = ModelRepository(db)
    success = repo.delete(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="model not found")

