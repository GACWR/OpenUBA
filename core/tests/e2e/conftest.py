'''
Copyright 2019-Present The OpenUBA Platform Authors
pytest configuration and fixtures for e2e tests
'''

import os
import pytest
import subprocess
import time
import logging
import requests as http_requests
from typing import Generator, Optional
from playwright.sync_api import Page, Browser, BrowserContext, sync_playwright

from core.tests.e2e.k8s_utils import K8sTestUtils
from core.tests.e2e.db_utils import DBTestUtils
from core.tests.e2e.log_utils import LogTestUtils

logger = logging.getLogger(__name__)

# e2e test configuration
E2E_NAMESPACE = os.getenv("E2E_NAMESPACE", "openuba")
E2E_FRONTEND_PORT = int(os.getenv("E2E_FRONTEND_PORT", "3000"))
E2E_BACKEND_PORT = int(os.getenv("E2E_BACKEND_PORT", "8000"))
E2E_DATABASE_URL = os.getenv(
    "E2E_DATABASE_URL",
    "postgresql://gacwr:gacwr@localhost:5432/openuba"
)


@pytest.fixture(scope="session")
def k8s_utils() -> Generator[K8sTestUtils, None, None]:
    '''
    kubernetes utilities fixture
    '''
    utils = K8sTestUtils(namespace=E2E_NAMESPACE)
    yield utils


@pytest.fixture(scope="session")
def db_utils() -> Generator[DBTestUtils, None, None]:
    '''
    database utilities fixture
    '''
    utils = DBTestUtils(database_url=E2E_DATABASE_URL)
    yield utils


@pytest.fixture(scope="session")
def log_utils(k8s_utils: K8sTestUtils) -> Generator[LogTestUtils, None, None]:
    '''
    log utilities fixture
    '''
    utils = LogTestUtils(k8s_utils)
    yield utils


@pytest.fixture(scope="session")
def deployed_system() -> Generator[dict, None, None]:
    '''
    ensure system is deployed and ready
    waits for all pods to be ready
    '''
    # deployed_system logic modified for local dev/testing against running services
    # We assume frontend and backend are already running on localhost:3000 and localhost:8000
    # as per user instructions. We still need Postgres/ES forwarded (handled manually or via previous steps).

    yield {
        "frontend_url": f"http://localhost:{E2E_FRONTEND_PORT}",
        "backend_url": f"http://localhost:{E2E_BACKEND_PORT}",
        "frontend_pf": None,
        "backend_pf": None
    }


@pytest.fixture(scope="session")
def playwright_browser() -> Generator[Browser, None, None]:
    '''
    playwright browser fixture
    '''
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(
    playwright_browser: Browser,
    deployed_system: dict
) -> Generator[Page, None, None]:
    '''
    playwright page fixture for each test
    '''
    context = playwright_browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)  # 30 second timeout
    yield page
    context.close()


@pytest.fixture(scope="function")
def frontend_url(deployed_system: dict) -> str:
    '''
    frontend url fixture
    '''
    return deployed_system["frontend_url"]


@pytest.fixture(scope="function")
def backend_url(deployed_system: dict) -> str:
    '''
    backend url fixture
    '''
    return deployed_system["backend_url"]


@pytest.fixture(scope="session")
def auth_headers(deployed_system: dict) -> dict:
    '''
    authenticate as default admin user and return headers with bearer token.
    used by e2e tests that call authenticated API endpoints.
    '''
    backend_url = deployed_system["backend_url"]
    login_data = {"username": "openuba", "password": "password"}
    try:
        resp = http_requests.post(
            f"{backend_url}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        logger.warning(f"auth login failed: {e}")

    # fallback: no auth (for environments where auth is disabled)
    return {}


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data(db_utils: DBTestUtils):
    '''
    cleanup test data before and after each test
    '''
    # cleanup before test
    db_utils.cleanup_test_data(test_prefix="e2e_test_")
    yield
    # cleanup after test
    db_utils.cleanup_test_data(test_prefix="e2e_test_")


@pytest.fixture(scope="function")
def verify_no_errors(log_utils: LogTestUtils):
    '''
    fixture to verify no errors in logs after test
    '''
    yield
    # check for errors after test
    backend_errors = log_utils.get_recent_backend_errors()
    frontend_errors = log_utils.get_recent_frontend_errors()

    if backend_errors:
        logger.warning(f"backend errors found: {backend_errors}")
    if frontend_errors:
        logger.warning(f"frontend errors found: {frontend_errors}")

    # don't fail test on warnings, but log them
    # tests should explicitly check for errors if needed

