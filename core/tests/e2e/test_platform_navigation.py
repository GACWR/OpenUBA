'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for platform navigation - verifies all new pages are accessible
'''

import pytest
import requests
from playwright.sync_api import Page


def test_sidebar_has_develop_section(page: Page, frontend_url: str):
    '''
    test that sidebar has the Develop navigation group
    '''
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")

    content = page.content().lower()
    assert "develop" in content or "workspaces" in content


def test_sidebar_has_monitor_section(page: Page, frontend_url: str):
    '''
    test that sidebar has the Monitor navigation group
    '''
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")

    content = page.content().lower()
    assert "monitor" in content or "jobs" in content


def test_navigate_to_workspaces(page: Page, frontend_url: str):
    '''
    test navigation to workspaces page
    '''
    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")
    assert "/workspaces" in page.url
    content = page.content().lower()
    assert "workspace" in content


def test_navigate_to_visualizations(page: Page, frontend_url: str):
    '''
    test navigation to visualizations page
    '''
    page.goto(f"{frontend_url}/visualizations")
    page.wait_for_load_state("networkidle")
    assert "/visualizations" in page.url
    content = page.content().lower()
    assert "visualization" in content


def test_navigate_to_dashboards(page: Page, frontend_url: str):
    '''
    test navigation to dashboards page
    '''
    page.goto(f"{frontend_url}/dashboards")
    page.wait_for_load_state("networkidle")
    assert "/dashboards" in page.url
    content = page.content().lower()
    assert "dashboard" in content


def test_navigate_to_experiments(page: Page, frontend_url: str):
    '''
    test navigation to experiments page
    '''
    page.goto(f"{frontend_url}/experiments")
    page.wait_for_load_state("networkidle")
    assert "/experiments" in page.url
    content = page.content().lower()
    assert "experiment" in content


def test_navigate_to_features(page: Page, frontend_url: str):
    '''
    test navigation to features page
    '''
    page.goto(f"{frontend_url}/features")
    page.wait_for_load_state("networkidle")
    assert "/features" in page.url
    content = page.content().lower()
    assert "feature" in content


def test_navigate_to_pipelines(page: Page, frontend_url: str):
    '''
    test navigation to pipelines page
    '''
    page.goto(f"{frontend_url}/pipelines")
    page.wait_for_load_state("networkidle")
    assert "/pipelines" in page.url
    content = page.content().lower()
    assert "pipeline" in content


def test_navigate_to_jobs(page: Page, frontend_url: str):
    '''
    test navigation to jobs page
    '''
    page.goto(f"{frontend_url}/jobs")
    page.wait_for_load_state("networkidle")
    assert "/jobs" in page.url
    content = page.content().lower()
    assert "job" in content


def test_navigate_to_datasets(page: Page, frontend_url: str):
    '''
    test navigation to datasets page
    '''
    page.goto(f"{frontend_url}/datasets")
    page.wait_for_load_state("networkidle")
    assert "/datasets" in page.url
    content = page.content().lower()
    assert "dataset" in content


def test_all_new_api_endpoints_respond(backend_url: str, auth_headers: dict):
    '''
    test that all new API endpoints respond with valid status codes
    '''
    endpoints = [
        ("GET", "/api/v1/workspaces"),
        ("GET", "/api/v1/jobs"),
        ("GET", "/api/v1/visualizations"),
        ("GET", "/api/v1/dashboards"),
        ("GET", "/api/v1/experiments"),
        ("GET", "/api/v1/features/groups"),
        ("GET", "/api/v1/pipelines"),
        ("GET", "/api/v1/datasets"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = requests.get(f"{backend_url}{path}", headers=auth_headers)
        assert resp.status_code == 200, f"{method} {path} returned {resp.status_code}: {resp.text}"


def test_health_check_still_works(backend_url: str):
    '''
    test that health endpoint still works after all new routers are registered
    '''
    resp = requests.get(f"{backend_url}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_root_endpoint_still_works(backend_url: str):
    '''
    test that root endpoint still returns API info
    '''
    resp = requests.get(f"{backend_url}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "OpenUBA API"
    assert "version" in data
