'''
Copyright 2019-Present The OpenUBA Platform Authors
chat service — multi-provider LLM streaming with system context
supports: ollama, openai, claude, gemini
'''

import json
import logging
import os
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx
from sqlalchemy import text

from core.db import get_db_context

logger = logging.getLogger(__name__)

# env var fallbacks for Ollama (backward compat)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://192.168.1.109:11435")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "lfm2.5-thinking")


class ChatService:
    '''
    multi-provider LLM chat service.
    reads provider config from integration_settings table,
    falls back to env vars for Ollama.
    '''

    def _load_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        '''load provider config from DB, fall back to env vars for ollama'''
        if not provider:
            provider = "ollama"

        try:
            with get_db_context() as db:
                row = db.execute(text(
                    "SELECT config, enabled FROM integration_settings "
                    "WHERE integration_type = :t"
                ), {"t": provider}).fetchone()

                if row and row[1]:  # enabled
                    config = dict(row[0]) if row[0] else {}
                    config["_provider"] = provider
                    return config
        except Exception as e:
            logger.warning(f"failed to load provider config for {provider}: {e}")

        # fallback: env vars for ollama
        if provider == "ollama":
            return {
                "_provider": "ollama",
                "host": OLLAMA_HOST,
                "model": OLLAMA_MODEL,
            }

        return {"_provider": provider}

    async def process_message_stream(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        '''
        stream LLM response tokens.
        dispatches to the right provider based on config.
        '''
        if not messages:
            yield "I didn't receive any message."
            return

        config = self._load_provider_config(provider)
        actual_provider = config.get("_provider", "ollama")

        # allow model override from request
        if model:
            config["model"] = model

        system_prompt = self._build_system_prompt(context)

        try:
            if actual_provider == "ollama":
                async for token in self._stream_ollama(system_prompt, messages, config):
                    yield token
            elif actual_provider == "openai":
                async for token in self._stream_openai(system_prompt, messages, config):
                    yield token
            elif actual_provider == "claude":
                async for token in self._stream_claude(system_prompt, messages, config):
                    yield token
            elif actual_provider == "gemini":
                async for token in self._stream_gemini(system_prompt, messages, config):
                    yield token
            else:
                yield f"Unknown provider: {actual_provider}"
        except httpx.ConnectError as e:
            logger.error(f"cannot connect to {actual_provider}: {e}")
            yield f"Cannot connect to {actual_provider}. Check your configuration in Settings > Integrations."
        except httpx.ReadTimeout:
            logger.error(f"{actual_provider} read timeout")
            yield "The LLM service timed out. Try a shorter question."
        except Exception as e:
            logger.error(f"{actual_provider} streaming error: {e}")
            yield f"An error occurred with {actual_provider}: {str(e)}"

    async def _stream_ollama(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        '''stream from Ollama /api/generate'''
        host = config.get("host", OLLAMA_HOST)
        model_name = config.get("model", OLLAMA_MODEL)
        prompt = self._format_prompt(system_prompt, messages)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{host.rstrip('/')}/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": True},
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"ollama returned {response.status_code}: {error_body}")
                    yield f"Ollama returned an error (HTTP {response.status_code})."
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            return
                    except json.JSONDecodeError:
                        continue

    async def _stream_openai(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        '''stream from OpenAI-compatible /v1/chat/completions'''
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        model_name = config.get("model", "gpt-4o")

        if not api_key:
            yield "OpenAI API key not configured. Go to Settings > Integrations to add it."
            return

        api_messages = self._build_openai_messages(system_prompt, messages)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": api_messages,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"openai returned {response.status_code}: {error_body}")
                    yield f"OpenAI returned an error (HTTP {response.status_code})."
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            yield token
                    except (json.JSONDecodeError, IndexError):
                        continue

    async def _stream_claude(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        '''stream from Anthropic /v1/messages'''
        api_key = config.get("api_key", "")
        model_name = config.get("model", "claude-sonnet-4-5-20250929")

        if not api_key:
            yield "Claude API key not configured. Go to Settings > Integrations to add it."
            return

        # claude uses separate system param, not in messages array
        api_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                api_messages.append({"role": role, "content": content})

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": api_messages,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"claude returned {response.status_code}: {error_body}")
                    yield f"Claude returned an error (HTTP {response.status_code})."
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        event = json.loads(data)
                        event_type = event.get("type", "")
                        if event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            token = delta.get("text", "")
                            if token:
                                yield token
                        elif event_type == "message_stop":
                            return
                    except json.JSONDecodeError:
                        continue

    async def _stream_gemini(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        '''stream from Google Gemini API'''
        api_key = config.get("api_key", "")
        model_name = config.get("model", "gemini-2.0-flash")

        if not api_key:
            yield "Gemini API key not configured. Go to Settings > Integrations to add it."
            return

        # build gemini contents format
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}],
            })

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}"
            f":streamGenerateContent?key={api_key}&alt=sse"
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": contents,
                    "systemInstruction": {
                        "parts": [{"text": system_prompt}],
                    },
                },
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"gemini returned {response.status_code}: {error_body}")
                    yield f"Gemini returned an error (HTTP {response.status_code})."
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                token = part.get("text", "")
                                if token:
                                    yield token
                    except json.JSONDecodeError:
                        continue

    def _build_openai_messages(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        '''build OpenAI-format message list with system prompt'''
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                api_messages.append({"role": role, "content": content})
        return api_messages

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        '''build a system prompt with current DB state and page context'''
        parts = [
            "You are the OpenUBA assistant. OpenUBA is an open-source User & Entity Behavior Analytics (UEBA) platform.",
            "You help security analysts understand anomalies, models, alerts, rules, cases, and entities in the system.",
            "Answer concisely and reference specific data when available. Use markdown formatting.",
        ]

        system_state = self._get_system_state()
        if system_state:
            parts.append("")
            parts.append("Current system state:")
            parts.append(system_state)

        if context:
            route = context.get("route", "")
            params = context.get("params") or {}
            route_context = self._get_route_context(route, params)
            if route_context:
                parts.append("")
                parts.append(route_context)
            if route:
                parts.append(f"\nThe user is currently viewing: {route}")

        return "\n".join(parts)

    def _get_system_state(self) -> str:
        '''query DB for high-level system stats'''
        try:
            with get_db_context() as db:
                anomaly_24h = db.execute(text(
                    "SELECT COUNT(*) FROM anomalies "
                    "WHERE timestamp > NOW() - INTERVAL '24 hours'"
                )).scalar() or 0

                models_active = db.execute(text(
                    "SELECT COUNT(*) FROM models WHERE enabled = true"
                )).scalar() or 0

                alerts_unacked = db.execute(text(
                    "SELECT COUNT(*) FROM alerts WHERE acknowledged = false"
                )).scalar() or 0

                cases_open = db.execute(text(
                    "SELECT COUNT(*) FROM cases WHERE status = 'open'"
                )).scalar() or 0

                rules_enabled = db.execute(text(
                    "SELECT COUNT(*) FROM rules WHERE enabled = true"
                )).scalar() or 0

                entities_count = db.execute(text(
                    "SELECT COUNT(*) FROM entities"
                )).scalar() or 0

                recent_rows = db.execute(text(
                    "SELECT entity_id, risk_score, anomaly_type, entity_type "
                    "FROM anomalies ORDER BY timestamp DESC LIMIT 5"
                )).fetchall()

                lines = [
                    f"- {anomaly_24h} anomalies in last 24h",
                    f"- {models_active} active models",
                    f"- {alerts_unacked} unacknowledged alerts",
                    f"- {cases_open} open cases",
                    f"- {rules_enabled} enabled rules",
                    f"- {entities_count} tracked entities",
                ]

                if recent_rows:
                    recent_items = []
                    for row in recent_rows:
                        entity_id, risk, atype, etype = row[0], row[1], row[2], row[3]
                        risk_val = float(risk) if risk is not None else 0
                        recent_items.append(
                            f"{etype} '{entity_id}' (risk: {risk_val:.0f}, type: {atype or 'unknown'})"
                        )
                    lines.append("- Recent anomalies: " + "; ".join(recent_items))

                return "\n".join(lines)

        except Exception as e:
            logger.warning(f"failed to gather system state: {e}")
            return ""

    def _get_route_context(self, route: str, params: Dict[str, str]) -> str:
        '''add extra context based on which page the user is on'''
        try:
            with get_db_context() as db:
                if route.startswith("/models/") and params.get("modelId"):
                    model_id = params["modelId"]
                    row = db.execute(text(
                        "SELECT name, version, status, enabled, description, framework "
                        "FROM models WHERE id = CAST(:id AS uuid)"
                    ), {"id": model_id}).fetchone()
                    if row:
                        name, ver, status, enabled, desc, fw = row
                        info = f"Viewing model: {name} v{ver} (status={status}, enabled={enabled}, framework={fw})"
                        if desc:
                            info += f"\nDescription: {desc}"
                        last_run = db.execute(text(
                            "SELECT mr.run_type, mr.status, mr.finished_at "
                            "FROM model_runs mr "
                            "JOIN model_versions mv ON mv.id = mr.model_version_id "
                            "WHERE mv.model_id = CAST(:id AS uuid) "
                            "ORDER BY mr.created_at DESC LIMIT 1"
                        ), {"id": model_id}).fetchone()
                        if last_run:
                            info += f"\nLast run: {last_run[0]} — {last_run[1]}"
                            if last_run[2]:
                                info += f" (finished {last_run[2]})"
                        return info

                elif route == "/models":
                    rows = db.execute(text(
                        "SELECT name, version, status FROM models WHERE enabled = true LIMIT 10"
                    )).fetchall()
                    if rows:
                        model_list = ", ".join(f"{r[0]} v{r[1]} ({r[2]})" for r in rows)
                        return f"Models page — active models: {model_list}"

                elif route == "/anomalies":
                    dist = db.execute(text(
                        "SELECT anomaly_type, COUNT(*) FROM anomalies "
                        "WHERE timestamp > NOW() - INTERVAL '7 days' "
                        "GROUP BY anomaly_type ORDER BY count DESC LIMIT 5"
                    )).fetchall()
                    if dist:
                        items = ", ".join(f"{r[0] or 'unknown'}: {r[1]}" for r in dist)
                        return f"Anomalies page — types in last 7d: {items}"

                elif route == "/cases":
                    rows = db.execute(text(
                        "SELECT title, severity, status FROM cases "
                        "WHERE status != 'closed' ORDER BY created_at DESC LIMIT 5"
                    )).fetchall()
                    if rows:
                        items = ", ".join(f"'{r[0]}' ({r[1]}, {r[2]})" for r in rows)
                        return f"Cases page — open/active: {items}"

                elif route == "/alerts":
                    dist = db.execute(text(
                        "SELECT severity, COUNT(*) FROM alerts "
                        "WHERE acknowledged = false "
                        "GROUP BY severity ORDER BY count DESC"
                    )).fetchall()
                    if dist:
                        items = ", ".join(f"{r[0]}: {r[1]}" for r in dist)
                        return f"Alerts page — unacknowledged by severity: {items}"

                elif route == "/rules":
                    rows = db.execute(text(
                        "SELECT name, enabled, rule_type FROM rules LIMIT 10"
                    )).fetchall()
                    if rows:
                        items = ", ".join(
                            f"{r[0]} ({'enabled' if r[1] else 'disabled'}, {r[2]})" for r in rows
                        )
                        return f"Rules page — rules: {items}"

                elif route == "/entities":
                    rows = db.execute(text(
                        "SELECT entity_id, entity_type, risk_score FROM entities "
                        "ORDER BY risk_score DESC LIMIT 5"
                    )).fetchall()
                    if rows:
                        items = ", ".join(
                            f"{r[0]} ({r[1]}, risk={float(r[2]) if r[2] else 0:.0f})" for r in rows
                        )
                        return f"Entities page — top risk: {items}"

        except Exception as e:
            logger.warning(f"failed to get route context for {route}: {e}")

        return ""

    def _format_prompt(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> str:
        '''
        format system prompt + conversation history into a single prompt string
        for Ollama /api/generate
        '''
        parts = [f"[System]\n{system_prompt}\n"]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                parts.append(f"[User]\n{content}\n")
            elif role == "assistant":
                parts.append(f"[Assistant]\n{content}\n")

        parts.append("[Assistant]\n")
        return "\n".join(parts)
