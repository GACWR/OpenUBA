'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e tests for display/dashboard flow
'''

import pytest
import requests
from playwright.sync_api import Page


def test_home_page_loads(page: Page, frontend_url: str):
    '''
    test that home page loads and displays dashboard
    '''
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")
    
    # check page title
    assert "OpenUBA" in page.title() or "Dashboard" in page.content()
    
    # check for summary statistics
    # the page should have stats displayed
    assert (
        page.locator("text=Total Models").is_visible() or
        page.locator("text=Models").is_visible() or
        page.locator("text=Anomalies").is_visible()
    )


def test_home_summary_api(backend_url: str):
    '''
    test home summary api endpoint
    '''
    response = requests.get(f"{backend_url}/api/v1/display/home/summary")
    assert response.status_code == 200
    summary = response.json()
    
    # verify summary has expected fields
    assert "total_models" in summary or "totalModels" in summary
    assert "total_anomalies" in summary or "totalAnomalies" in summary
    assert "open_cases" in summary or "openCases" in summary


def test_navigation_links(page: Page, frontend_url: str):
    '''
    test navigation links work
    '''
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")
    
    # test navigation to models
    if page.locator("text=Models").is_visible():
        page.click("text=Models")
        page.wait_for_load_state("networkidle")
        assert "/models" in page.url or "Models" in page.content()
    
    # go back and test anomalies
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")
    if page.locator("text=Anomalies").is_visible():
        page.click("text=Anomalies")
        page.wait_for_load_state("networkidle")
        assert "/anomalies" in page.url or "Anomalies" in page.content()
    
    # go back and test cases
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")
    if page.locator("text=Cases").is_visible():
        page.click("text=Cases")
        page.wait_for_load_state("networkidle")
        assert "/cases" in page.url or "Cases" in page.content()


def test_display_endpoint_via_api(backend_url: str):
    '''
    test display endpoint via api
    '''
    # test different display types
    display_types = ["home/summary"]
    
    for display_type in display_types:
        response = requests.get(f"{backend_url}/api/v1/display/{display_type}")
        assert response.status_code == 200
        data = response.json()
        assert data is not None

