'''
Copyright 2019-Present The OpenUBA Platform Authors
settings api router — CRUD for integration settings (LLM providers, ES, Spark)
'''

import logging
from typing import Optional, Dict, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from core.db import get_db_context
from core.auth import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_INTEGRATION_TYPES = {"ollama", "openai", "claude", "gemini", "elasticsearch", "spark"}


class IntegrationConfigUpdate(BaseModel):
    enabled: bool = False
    config: Dict[str, Any] = {}


class IntegrationSettingResponse(BaseModel):
    integration_type: str
    enabled: bool
    config: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/settings/integrations")
async def list_integrations(
    current_user: dict = Depends(require_permission("settings")),
):
    '''list all integration settings'''
    with get_db_context() as db:
        rows = db.execute(text(
            "SELECT integration_type, enabled, config, "
            "created_at::text, updated_at::text "
            "FROM integration_settings ORDER BY integration_type"
        )).fetchall()

    results = []
    seen_types = set()
    for row in rows:
        seen_types.add(row[0])
        # strip api keys from response for security
        config = dict(row[2]) if row[2] else {}
        safe_config = _mask_sensitive_fields(config)
        results.append({
            "integration_type": row[0],
            "enabled": row[1],
            "config": safe_config,
            "created_at": row[3],
            "updated_at": row[4],
        })

    # include defaults for types not yet configured
    for itype in sorted(VALID_INTEGRATION_TYPES - seen_types):
        results.append({
            "integration_type": itype,
            "enabled": False,
            "config": {},
            "created_at": None,
            "updated_at": None,
        })

    return results


@router.get("/settings/integrations/{integration_type}")
async def get_integration(
    integration_type: str,
    current_user: dict = Depends(require_permission("settings")),
):
    '''get a single integration setting'''
    if integration_type not in VALID_INTEGRATION_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid integration type: {integration_type}")

    with get_db_context() as db:
        row = db.execute(text(
            "SELECT integration_type, enabled, config, "
            "created_at::text, updated_at::text "
            "FROM integration_settings WHERE integration_type = :t"
        ), {"t": integration_type}).fetchone()

    if not row:
        return {
            "integration_type": integration_type,
            "enabled": False,
            "config": {},
            "created_at": None,
            "updated_at": None,
        }

    config = dict(row[2]) if row[2] else {}
    return {
        "integration_type": row[0],
        "enabled": row[1],
        "config": _mask_sensitive_fields(config),
        "created_at": row[3],
        "updated_at": row[4],
    }


@router.put("/settings/integrations/{integration_type}")
async def update_integration(
    integration_type: str,
    body: IntegrationConfigUpdate,
    current_user: dict = Depends(require_permission("settings", "write")),
):
    '''create or update an integration setting'''
    if integration_type not in VALID_INTEGRATION_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid integration type: {integration_type}")

    with get_db_context() as db:
        # upsert
        db.execute(text(
            "INSERT INTO integration_settings (integration_type, enabled, config) "
            "VALUES (:t, :e, CAST(:c AS jsonb)) "
            "ON CONFLICT (integration_type) DO UPDATE SET "
            "enabled = :e, config = CAST(:c AS jsonb), "
            "updated_at = CURRENT_TIMESTAMP"
        ), {
            "t": integration_type,
            "e": body.enabled,
            "c": _serialize_config(body.config),
        })
        db.commit()

        # read back
        row = db.execute(text(
            "SELECT integration_type, enabled, config, "
            "created_at::text, updated_at::text "
            "FROM integration_settings WHERE integration_type = :t"
        ), {"t": integration_type}).fetchone()

    config = dict(row[2]) if row[2] else {}
    return {
        "integration_type": row[0],
        "enabled": row[1],
        "config": _mask_sensitive_fields(config),
        "created_at": row[3],
        "updated_at": row[4],
    }


@router.get("/settings/integrations/{integration_type}/test")
async def test_integration(
    integration_type: str,
    current_user: dict = Depends(require_permission("settings")),
):
    '''test connectivity for an integration'''
    if integration_type not in VALID_INTEGRATION_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid integration type: {integration_type}")

    # load config from DB
    with get_db_context() as db:
        row = db.execute(text(
            "SELECT config FROM integration_settings WHERE integration_type = :t"
        ), {"t": integration_type}).fetchone()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail=f"{integration_type} not configured")

    config = dict(row[0])

    try:
        if integration_type == "ollama":
            return await _test_ollama(config)
        elif integration_type == "openai":
            return await _test_openai(config)
        elif integration_type == "claude":
            return await _test_claude(config)
        elif integration_type == "gemini":
            return await _test_gemini(config)
        elif integration_type == "elasticsearch":
            return await _test_elasticsearch(config)
        elif integration_type == "spark":
            return await _test_spark(config)
    except Exception as e:
        logger.error(f"test {integration_type} failed: {e}")
        return {"status": "error", "message": str(e)}


async def _test_ollama(config: dict) -> dict:
    host = config.get("host", "")
    if not host:
        return {"status": "error", "message": "host not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{host.rstrip('/')}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            model_names = [m.get("name", "") for m in data.get("models", [])]
            return {"status": "connected", "models": model_names}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


async def _test_openai(config: dict) -> dict:
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://api.openai.com/v1")
    if not api_key:
        return {"status": "error", "message": "api_key not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code == 200:
            return {"status": "connected"}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


async def _test_claude(config: dict) -> dict:
    api_key = config.get("api_key", "")
    if not api_key:
        return {"status": "error", "message": "api_key not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        if resp.status_code == 200:
            return {"status": "connected"}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


async def _test_gemini(config: dict) -> dict:
    api_key = config.get("api_key", "")
    if not api_key:
        return {"status": "error", "message": "api_key not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        )
        if resp.status_code == 200:
            return {"status": "connected"}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


async def _test_elasticsearch(config: dict) -> dict:
    host = config.get("host", "")
    if not host:
        return {"status": "error", "message": "host not configured"}
    headers = {}
    api_key = config.get("api_key", "")
    if api_key:
        headers["Authorization"] = f"ApiKey {api_key}"
    verify_ssl = config.get("verify_ssl", True)
    async with httpx.AsyncClient(timeout=10.0, verify=verify_ssl) as client:
        resp = await client.get(host.rstrip("/"), headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "connected",
                "cluster_name": data.get("cluster_name", ""),
                "version": data.get("version", {}).get("number", ""),
            }
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


async def _test_spark(config: dict) -> dict:
    master_url = config.get("master_url", "")
    if not master_url:
        return {"status": "error", "message": "master_url not configured"}
    # spark master UI is usually on port 8080 — try a simple HTTP check
    # convert spark:// to http:// for the web UI
    http_url = master_url.replace("spark://", "http://")
    if ":7077" in http_url:
        http_url = http_url.replace(":7077", ":8080")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{http_url.rstrip('/')}/json/")
        if resp.status_code == 200:
            return {"status": "connected"}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}


def _mask_sensitive_fields(config: dict) -> dict:
    '''mask api keys in config for safe display'''
    masked = dict(config)
    for key in ("api_key",):
        if key in masked and masked[key]:
            val = str(masked[key])
            if len(val) > 8:
                masked[key] = val[:4] + "..." + val[-4:]
            else:
                masked[key] = "****"
    return masked


def _serialize_config(config: dict) -> str:
    '''serialize config dict to JSON string for postgres'''
    import json
    return json.dumps(config)
