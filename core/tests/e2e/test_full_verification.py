'''
Copyright 2019-Present The OpenUBA Platform Authors
full end-to-end verification test with screenshots and DOM content validation
'''

import os
import pytest
import requests
from playwright.sync_api import Page
from uuid import uuid4

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


@pytest.fixture(scope="module", autouse=True)
def setup_screenshots_dir():
    '''create screenshots directory'''
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def ui_login(page: Page, frontend_url: str):
    '''log in via the UI so subsequent page navigations show actual content'''
    page.goto(f"{frontend_url}/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[placeholder="Enter username"]', "openuba")
    page.fill('input[placeholder="Enter password"]', "password")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{frontend_url}/", timeout=10000)
    page.wait_for_load_state("networkidle")


# ─── API + UI: Workspaces ─────────────────────────────────────────────────────

def test_workspace_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create workspace via API, verify in UI with screenshot'''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/workspaces/launch",
        json={"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create workspace failed: {resp.text}"
    ws = resp.json()
    assert ws["status"] == "pending"
    assert ws["hardware_tier"] == "cpu-small"

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "workspaces_page.png"), full_page=True)

    content = page.content().lower()
    assert "workspace" in content, "Workspaces page missing 'workspace' in DOM"
    # verify we're NOT on the login page
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # stop workspace
    ws_id = ws["id"]
    stop_resp = requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"

    # delete workspace
    del_resp = requests.delete(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert del_resp.status_code == 204


# ─── API + UI: Jobs ───────────────────────────────────────────────────────────

def test_jobs_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create model + job via API, verify in UI with screenshot'''
    # create a model first (jobs require model_id)
    model_name = f"e2e_test_model_{uuid4().hex[:8]}"
    model_resp = requests.post(
        f"{backend_url}/api/v1/models",
        json={"name": model_name, "version": "1.0.0", "source_type": "local_fs"},
        headers=auth_headers
    )
    assert model_resp.status_code == 201, f"Create model failed: {model_resp.text}"
    model_id = model_resp.json()["id"]

    job_name = f"e2e_test_job_{uuid4().hex[:8]}"
    job_resp = requests.post(
        f"{backend_url}/api/v1/jobs",
        json={"name": job_name, "model_id": model_id, "job_type": "training", "hardware_tier": "cpu-small"},
        headers=auth_headers
    )
    assert job_resp.status_code == 201, f"Create job failed: {job_resp.text}"
    job = job_resp.json()
    assert job["status"] == "pending"
    assert job["job_type"] == "training"
    job_id = job["id"]

    # update job status
    update_resp = requests.patch(
        f"{backend_url}/api/v1/jobs/{job_id}",
        json={"status": "running"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "running"

    # post internal metric (no auth)
    metric_resp = requests.post(
        f"{backend_url}/api/v1/internal/metrics/{job_id}",
        json={"metric_name": "loss", "metric_value": 0.42, "epoch": 1, "step": 100}
    )
    assert metric_resp.status_code == 201

    # post internal log (no auth)
    log_resp = requests.post(
        f"{backend_url}/api/v1/internal/logs/{job_id}",
        json={"message": "training epoch 1 started", "level": "info"}
    )
    assert log_resp.status_code == 201

    # verify metrics
    metrics_resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}/metrics", headers=auth_headers)
    assert metrics_resp.status_code == 200
    assert len(metrics_resp.json()) > 0

    # verify logs
    logs_resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}/logs", headers=auth_headers)
    assert logs_resp.status_code == 200
    assert len(logs_resp.json()) > 0

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/jobs")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "jobs_page.png"), full_page=True)

    content = page.content().lower()
    assert "job" in content, "Jobs page missing 'job' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/jobs/{job_id}", headers=auth_headers)


# ─── API + UI: Visualizations ─────────────────────────────────────────────────

def test_visualizations_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create visualization via API, publish it, verify in UI with screenshot'''
    viz_name = f"e2e_test_viz_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/visualizations",
        json={"name": viz_name, "backend": "recharts", "output_type": "html", "config": {"chart_type": "bar"}},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create viz failed: {resp.text}"
    viz = resp.json()
    viz_id = viz["id"]
    assert viz["backend"] == "recharts"
    assert viz["published"] == False

    # update
    update_resp = requests.put(
        f"{backend_url}/api/v1/visualizations/{viz_id}",
        json={"description": "updated viz description"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated viz description"

    # publish
    pub_resp = requests.post(f"{backend_url}/api/v1/visualizations/{viz_id}/publish", headers=auth_headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["published"] == True

    # cannot publish again
    pub2_resp = requests.post(f"{backend_url}/api/v1/visualizations/{viz_id}/publish", headers=auth_headers)
    assert pub2_resp.status_code == 400

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/visualizations")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "visualizations_page.png"), full_page=True)

    content = page.content().lower()
    assert "visualization" in content, "Visualizations page missing 'visualization' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/visualizations/{viz_id}", headers=auth_headers)


# ─── API + UI: Dashboards ─────────────────────────────────────────────────────

def test_dashboards_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create dashboard via API, verify in UI with screenshot'''
    dash_name = f"e2e_test_dash_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/dashboards",
        json={"name": dash_name, "description": "test dashboard", "layout": [{"type": "row", "widgets": []}]},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create dashboard failed: {resp.text}"
    dash = resp.json()
    dash_id = dash["id"]
    assert dash["published"] == False

    # update
    update_resp = requests.put(
        f"{backend_url}/api/v1/dashboards/{dash_id}",
        json={"description": "updated dashboard"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated dashboard"

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/dashboards")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "dashboards_page.png"), full_page=True)

    content = page.content().lower()
    assert "dashboard" in content, "Dashboards page missing 'dashboard' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/dashboards/{dash_id}", headers=auth_headers)


# ─── API + UI: Experiments ─────────────────────────────────────────────────────

def test_experiments_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create experiment with runs via API, verify in UI with screenshot'''
    exp_name = f"e2e_test_exp_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/experiments",
        json={"name": exp_name, "description": "test experiment"},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create experiment failed: {resp.text}"
    exp = resp.json()
    exp_id = exp["id"]

    # add runs
    for lr, acc in [(0.001, 0.95), (0.01, 0.90)]:
        run_resp = requests.post(
            f"{backend_url}/api/v1/experiments/{exp_id}/runs",
            json={"parameters": {"learning_rate": lr}, "metrics": {"accuracy": acc}},
            headers=auth_headers
        )
        assert run_resp.status_code == 201, f"Add run failed: {run_resp.text}"

    # list runs
    runs_resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}/runs", headers=auth_headers)
    assert runs_resp.status_code == 200
    assert len(runs_resp.json()) == 2

    # compare runs
    compare_resp = requests.get(f"{backend_url}/api/v1/experiments/{exp_id}/compare", headers=auth_headers)
    assert compare_resp.status_code == 200
    assert len(compare_resp.json()) == 2

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/experiments")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "experiments_page.png"), full_page=True)

    content = page.content().lower()
    assert "experiment" in content, "Experiments page missing 'experiment' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/experiments/{exp_id}", headers=auth_headers)


# ─── API + UI: Features ───────────────────────────────────────────────────────

def test_features_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create feature group and features via API, verify in UI with screenshot'''
    group_name = f"e2e_test_fg_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/features/groups",
        json={"name": group_name, "description": "test feature group", "entity": "user"},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create feature group failed: {resp.text}"
    group = resp.json()
    group_id = group["id"]
    assert group["entity"] == "user"

    # get by name
    name_resp = requests.get(f"{backend_url}/api/v1/features/groups/name/{group_name}", headers=auth_headers)
    assert name_resp.status_code == 200
    assert name_resp.json()["name"] == group_name

    # add features
    for fname in ["login_count", "session_duration"]:
        feat_resp = requests.post(
            f"{backend_url}/api/v1/features/groups/{group_id}/features",
            json={"name": f"e2e_test_{fname}_{uuid4().hex[:8]}", "dtype": "float64", "transform": "zscore"},
            headers=auth_headers
        )
        assert feat_resp.status_code == 201, f"Add feature failed: {feat_resp.text}"

    # list features
    feats_resp = requests.get(f"{backend_url}/api/v1/features/groups/{group_id}/features", headers=auth_headers)
    assert feats_resp.status_code == 200
    assert len(feats_resp.json()) == 2

    # duplicate name rejected
    dup_resp = requests.post(
        f"{backend_url}/api/v1/features/groups",
        json={"name": group_name, "description": "duplicate", "entity": "user"},
        headers=auth_headers
    )
    assert dup_resp.status_code == 400

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/features")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "features_page.png"), full_page=True)

    content = page.content().lower()
    assert "feature" in content, "Features page missing 'feature' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/features/groups/{group_id}", headers=auth_headers)


# ─── API + UI: Pipelines ──────────────────────────────────────────────────────

def test_pipelines_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create pipeline, run it, verify in UI with screenshot'''
    pipe_name = f"e2e_test_pipe_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/pipelines",
        json={
            "name": pipe_name,
            "description": "test pipeline",
            "steps": [{"type": "training", "config": {"epochs": 10}}, {"type": "inference"}]
        },
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create pipeline failed: {resp.text}"
    pipe = resp.json()
    pipe_id = pipe["id"]

    # update pipeline
    update_resp = requests.put(
        f"{backend_url}/api/v1/pipelines/{pipe_id}",
        json={"description": "updated pipeline"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated pipeline"

    # run pipeline
    run_resp = requests.post(f"{backend_url}/api/v1/pipelines/{pipe_id}/run", headers=auth_headers)
    assert run_resp.status_code == 201, f"Run pipeline failed: {run_resp.text}"
    assert run_resp.json()["status"] == "pending"

    # list runs
    runs_resp = requests.get(f"{backend_url}/api/v1/pipelines/{pipe_id}/runs", headers=auth_headers)
    assert runs_resp.status_code == 200
    assert len(runs_resp.json()) >= 1

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/pipelines")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "pipelines_page.png"), full_page=True)

    content = page.content().lower()
    assert "pipeline" in content, "Pipelines page missing 'pipeline' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/pipelines/{pipe_id}", headers=auth_headers)


# ─── API + UI: Datasets ───────────────────────────────────────────────────────

def test_datasets_full_flow(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create dataset via API, update, verify in UI with screenshot'''
    ds_name = f"e2e_test_ds_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/datasets",
        json={"name": ds_name, "description": "test dataset", "format": "csv"},
        headers=auth_headers
    )
    assert resp.status_code == 201, f"Create dataset failed: {resp.text}"
    ds = resp.json()
    ds_id = ds["id"]
    assert ds["format"] == "csv"

    # get by id
    get_resp = requests.get(f"{backend_url}/api/v1/datasets/{ds_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == ds_name

    # update
    update_resp = requests.patch(
        f"{backend_url}/api/v1/datasets/{ds_id}",
        json={"description": "updated description"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated description"

    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/datasets")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "datasets_page.png"), full_page=True)

    content = page.content().lower()
    assert "dataset" in content, "Datasets page missing 'dataset' in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/datasets/{ds_id}", headers=auth_headers)


# ─── Navigation & DOM Verification ────────────────────────────────────────────

def test_homepage_screenshot(page: Page, frontend_url: str):
    '''take screenshot of homepage and verify DOM'''
    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "homepage.png"), full_page=True)

    content = page.content().lower()
    assert "openuba" in content or "open" in content, "Homepage missing platform name in DOM"
    assert "sign in to your account" not in content, "Still on login page - auth failed"


def test_all_new_pages_dom_content(page: Page, frontend_url: str):
    '''navigate to every new page, take screenshot, verify DOM has meaningful content'''
    ui_login(page, frontend_url)
    pages_to_check = [
        ("workspaces", ["workspace"]),
        ("jobs", ["job"]),
        ("visualizations", ["visualization"]),
        ("dashboards", ["dashboard"]),
        ("experiments", ["experiment"]),
        ("features", ["feature"]),
        ("pipelines", ["pipeline"]),
        ("datasets", ["dataset"]),
    ]

    for page_path, expected_words in pages_to_check:
        page.goto(f"{frontend_url}/{page_path}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"nav_{page_path}.png"), full_page=True)

        content = page.content().lower()
        assert "sign in to your account" not in content, f"Page /{page_path} still on login page"
        for word in expected_words:
            assert word in content, f"Page /{page_path} missing '{word}' in DOM content"

        # verify page didn't return a 404 or error page
        assert "404" not in page.title().lower(), f"Page /{page_path} returned 404"
        assert "error" not in page.title().lower(), f"Page /{page_path} has error in title"


def test_all_api_endpoints_crud(backend_url: str, auth_headers: dict):
    '''verify all new API endpoints support full CRUD where expected'''
    # verify list endpoints return arrays
    list_endpoints = [
        "/api/v1/workspaces",
        "/api/v1/jobs",
        "/api/v1/visualizations",
        "/api/v1/dashboards",
        "/api/v1/experiments",
        "/api/v1/features/groups",
        "/api/v1/pipelines",
        "/api/v1/datasets",
    ]
    for endpoint in list_endpoints:
        resp = requests.get(f"{backend_url}{endpoint}", headers=auth_headers)
        assert resp.status_code == 200, f"GET {endpoint} returned {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), f"GET {endpoint} did not return a list"

    # verify 404 for non-existent resources
    fake_id = "00000000-0000-0000-0000-000000000000"
    not_found_endpoints = [
        f"/api/v1/workspaces/{fake_id}",
        f"/api/v1/jobs/{fake_id}",
        f"/api/v1/visualizations/{fake_id}",
        f"/api/v1/dashboards/{fake_id}",
        f"/api/v1/experiments/{fake_id}",
        f"/api/v1/features/groups/{fake_id}",
        f"/api/v1/pipelines/{fake_id}",
        f"/api/v1/datasets/{fake_id}",
    ]
    for endpoint in not_found_endpoints:
        resp = requests.get(f"{backend_url}{endpoint}", headers=auth_headers)
        assert resp.status_code == 404, f"GET {endpoint} should return 404 but got {resp.status_code}"

    # verify health still works
    health_resp = requests.get(f"{backend_url}/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"


# ─── Deep-dive: Visualization Detail with Actual Chart ────────────────────────

def test_visualization_detail_with_chart(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create visualization with chart data, navigate to detail page, screenshot the rendered chart'''
    import time
    viz_name = f"e2e_test_viz_chart_{uuid4().hex[:8]}"
    chart_data = [
        {"name": "Login Anomalies", "value": 142},
        {"name": "Access Violations", "value": 87},
        {"name": "Data Exfiltration", "value": 23},
        {"name": "Privilege Escalation", "value": 56},
        {"name": "Lateral Movement", "value": 34},
        {"name": "Credential Abuse", "value": 98},
    ]
    resp = requests.post(
        f"{backend_url}/api/v1/visualizations",
        json={
            "name": viz_name,
            "backend": "recharts",
            "output_type": "html",
            "description": "UBA threat category distribution",
            "config": {"chart_type": "bar", "x_key": "name", "y_key": "value"},
            "data": {"values": chart_data},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Create viz failed: {resp.text}"
    viz_id = resp.json()["id"]

    # publish it
    pub_resp = requests.post(f"{backend_url}/api/v1/visualizations/{viz_id}/publish", headers=auth_headers)
    assert pub_resp.status_code == 200

    # navigate to detail page
    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/visualizations/{viz_id}")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # allow recharts to render
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "viz_detail_bar_chart.png"), full_page=True)

    content = page.content().lower()
    assert "sign in to your account" not in content, "Still on login page"
    assert "chart preview" in content, "Visualization detail page missing chart preview section"
    assert viz_name.lower() in content, f"Visualization name '{viz_name}' not found on detail page"
    assert "recharts" in content, "Backend label 'recharts' not visible"

    # also create a line chart visualization
    viz_name_line = f"e2e_test_viz_line_{uuid4().hex[:8]}"
    line_data = [
        {"name": "Week 1", "value": 12},
        {"name": "Week 2", "value": 19},
        {"name": "Week 3", "value": 15},
        {"name": "Week 4", "value": 28},
        {"name": "Week 5", "value": 22},
        {"name": "Week 6", "value": 35},
    ]
    line_resp = requests.post(
        f"{backend_url}/api/v1/visualizations",
        json={
            "name": viz_name_line,
            "backend": "recharts",
            "output_type": "html",
            "description": "Risk score trend over time",
            "config": {"chart_type": "line", "x_key": "name", "y_key": "value"},
            "data": {"values": line_data},
        },
        headers=auth_headers,
    )
    assert line_resp.status_code == 201
    line_viz_id = line_resp.json()["id"]

    page.goto(f"{frontend_url}/visualizations/{line_viz_id}")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "viz_detail_line_chart.png"), full_page=True)

    content = page.content().lower()
    assert viz_name_line.lower() in content
    assert "chart preview" in content

    # cleanup
    requests.delete(f"{backend_url}/api/v1/visualizations/{viz_id}", headers=auth_headers)
    requests.delete(f"{backend_url}/api/v1/visualizations/{line_viz_id}", headers=auth_headers)


# ─── Deep-dive: Dashboard Detail with Actual Panels ──────────────────────────

def test_dashboard_detail_with_panels(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''create dashboard with multiple chart panels, navigate to detail page, screenshot the rendered dashboard'''
    import time
    dash_name = f"e2e_test_dash_panels_{uuid4().hex[:8]}"
    layout = [
        {
            "title": "Anomaly Scores by User",
            "chart_type": "bar",
            "color": "#8884d8",
            "data": [
                {"name": "user_001", "value": 87},
                {"name": "user_042", "value": 92},
                {"name": "user_108", "value": 65},
                {"name": "user_227", "value": 78},
            ],
        },
        {
            "title": "Risk Trend (30 days)",
            "chart_type": "line",
            "color": "#82ca9d",
            "data": [
                {"name": "Day 1", "value": 42},
                {"name": "Day 7", "value": 55},
                {"name": "Day 14", "value": 38},
                {"name": "Day 21", "value": 67},
                {"name": "Day 30", "value": 51},
            ],
        },
        {
            "title": "Threat Distribution",
            "chart_type": "pie",
            "data": [
                {"name": "Insider", "value": 45},
                {"name": "External", "value": 30},
                {"name": "Compromised", "value": 25},
            ],
        },
        {
            "title": "Active Alerts",
            "chart_type": "stat",
            "stat_value": 23,
            "stat_label": "open alerts",
        },
    ]

    resp = requests.post(
        f"{backend_url}/api/v1/dashboards",
        json={
            "name": dash_name,
            "description": "Security operations dashboard with multiple panels",
            "layout": layout,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Create dashboard failed: {resp.text}"
    dash_id = resp.json()["id"]

    # navigate to detail page
    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/dashboards/{dash_id}")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # allow charts to render
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "dashboard_detail_panels.png"), full_page=True)

    content = page.content().lower()
    assert "sign in to your account" not in content, "Still on login page"
    assert dash_name.lower() in content, f"Dashboard name '{dash_name}' not found"
    assert "anomaly scores" in content, "Panel title 'Anomaly Scores by User' not visible"
    assert "risk trend" in content, "Panel title 'Risk Trend' not visible"
    assert "threat distribution" in content, "Panel title 'Threat Distribution' not visible"
    assert "active alerts" in content, "Panel title 'Active Alerts' not visible"

    # cleanup
    requests.delete(f"{backend_url}/api/v1/dashboards/{dash_id}", headers=auth_headers)


# ─── Deep-dive: Workspace Detail Page ─────────────────────────────────────────

def test_workspace_detail_page(page: Page, frontend_url: str, backend_url: str, auth_headers: dict):
    '''launch workspace, navigate to detail page, screenshot the workspace view'''
    import time
    ws_name = f"e2e_test_ws_detail_{uuid4().hex[:8]}"
    resp = requests.post(
        f"{backend_url}/api/v1/workspaces/launch",
        json={"name": ws_name, "environment": "default", "hardware_tier": "cpu-small", "ide": "jupyterlab"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Create workspace failed: {resp.text}"
    ws = resp.json()
    ws_id = ws["id"]

    # wait for workspace to become running (poll up to 60s)
    status = ws["status"]
    for _ in range(12):
        time.sleep(5)
        check = requests.get(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
        if check.ok:
            status = check.json().get("status", status)
            if status == "running":
                break

    # navigate to detail page regardless of status (screenshot what we get)
    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/workspaces/{ws_id}")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "workspace_detail.png"), full_page=True)

    content = page.content().lower()
    assert "sign in to your account" not in content, "Still on login page"
    assert ws_name.lower() in content, f"Workspace name '{ws_name}' not found on detail page"
    assert "workspace details" in content, "Missing 'Workspace Details' section"
    assert "hardware tier" in content, "Missing 'Hardware Tier' field"
    assert "cpu-small" in content, "Hardware tier value not displayed"

    # if workspace reached running, we should see the iframe
    if status == "running":
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "workspace_running_jupyterlab.png"), full_page=True)
        assert "workspace environment" in content, "Missing embedded workspace environment section"

    # cleanup
    requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)
    requests.delete(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
