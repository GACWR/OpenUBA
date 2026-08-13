'''
Copyright 2019-Present The OpenUBA Platform Authors
lifespan async-safety tests (regression for #140)

verifies the fastapi lifespan uses a non-blocking backoff
(await asyncio.sleep) instead of a blocking time.sleep that
would stall the event loop during db reconnection attempts.
'''

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import fastapi_app


def test_lifespan_source_has_no_blocking_sleep():
    '''
    static guard: the lifespan retry loop must not call time.sleep,
    and must await asyncio.sleep for its backoff
    '''
    source = inspect.getsource(fastapi_app.lifespan)
    assert "time.sleep" not in source, "lifespan must not block the event loop with time.sleep"
    assert "await asyncio.sleep" in source, "lifespan backoff must use await asyncio.sleep"


@pytest.mark.asyncio
async def test_lifespan_retries_with_non_blocking_sleep(monkeypatch):
    '''
    functional guard: when init_db fails once then succeeds, the lifespan
    retries and backs off via a non-blocking await asyncio.sleep call
    '''
    # kubernetes mode skips local ingestion + local postgraphile bootstrap
    monkeypatch.setenv("EXECUTION_MODE", "kubernetes")
    monkeypatch.setenv("ENABLE_GRAPHQL", "false")

    init_db_mock = MagicMock(side_effect=[RuntimeError("db not ready"), None])
    sleep_mock = AsyncMock()

    with patch.object(fastapi_app, "init_db", init_db_mock), \
         patch.object(fastapi_app, "seed_defaults", MagicMock()), \
         patch.object(fastapi_app, "ModelInstaller", MagicMock()), \
         patch.object(fastapi_app, "ModelScheduler", MagicMock()), \
         patch.object(fastapi_app.asyncio, "sleep", sleep_mock):
        async with fastapi_app.lifespan(fastapi_app.app):
            pass

    # init_db was retried (failed once, then succeeded)
    assert init_db_mock.call_count == 2
    # backoff happened exactly once, via the non-blocking await path
    sleep_mock.assert_awaited_once_with(5)
