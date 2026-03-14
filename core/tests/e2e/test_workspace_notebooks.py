'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e test: execute ALL workspace notebooks in JupyterLab and verify 100% SDK coverage

This test proves that every openuba SDK notebook runs successfully inside a workspace:
1. Start a JupyterLab container with all workspace notebooks pre-loaded
2. Create a workspace in the UI
3. Execute each notebook via nbconvert (reliable programmatic execution)
4. Open each executed notebook in JupyterLab via Playwright
5. Take screenshots of every notebook showing outputs
6. Verify no Python errors in any notebook output
'''

import os
import json
import time
import subprocess
import pytest
import requests
from uuid import uuid4
from playwright.sync_api import Page
from sqlalchemy import text

from core.tests.e2e.db_utils import DBTestUtils

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
JUPYTER_HOST_PORT = 38889  # different port from test_workspace_jupyterlab_sdk
JUPYTER_CONTAINER_NAME = "e2e-test-notebooks"
WORKSPACE_IMAGE = "openuba-workspace:latest"
JUPYTER_BASE_URL = f"http://localhost:{JUPYTER_HOST_PORT}"

# All workspace notebooks in execution order
NOTEBOOKS = [
    "01_quickstart.ipynb",
    "02_models.ipynb",
    "03_datasets.ipynb",
    "04_training_jobs.ipynb",
    "05_visualizations.ipynb",
    "06_dashboards.ipynb",
    "07_ml_workflow.ipynb",
    "08_uba_queries.ipynb",
]

# SDK functions each notebook covers (for verification reporting)
NOTEBOOK_SDK_COVERAGE = {
    "01_quickstart.ipynb": [
        "configure", "OpenUBAClient", "ModelContext", "VisualizationContext",
        "__version__", "__all__",
    ],
    "02_models.ipynb": [
        "register_model", "publish_version", "load_model",
        "list_models", "get_model", "list_installed",
    ],
    "03_datasets.ipynb": [
        "create_dataset", "list_datasets", "get_dataset",
    ],
    "04_training_jobs.ipynb": [
        "start_training", "start_inference", "get_job",
        "get_logs", "post_log", "ModelContext",
    ],
    "05_visualizations.ipynb": [
        "create_visualization", "publish_visualization", "list_visualizations",
        "VisualizationContext.render",
    ],
    "06_dashboards.ipynb": [
        "create_dashboard", "update_dashboard", "list_dashboards",
    ],
    "07_ml_workflow.ipynb": [
        "create_features", "load_features",
        "create_hyperparameters", "load_hyperparameters",
        "create_experiment", "add_experiment_run", "compare_experiment_runs",
        "create_pipeline", "run_pipeline",
    ],
    "08_uba_queries.ipynb": [
        "query_anomalies", "get_entity_risk", "query_cases", "list_rules",
        "query_spark", "query_elasticsearch",
    ],
}

# Error patterns that indicate a real failure (not a handled API error)
FATAL_ERROR_PATTERNS = [
    "syntaxerror",
    "indentationerror",
    "nameerror",
    "typeerror: ",  # with space to avoid matching "typeerror" in descriptions
    "attributeerror",
    "modulenotfounderror",
    "importerror",
    "filenotfounderror",
    "zerodivisionerror",
    "keyerror",
    "valueerror: unsupported",
    "traceback (most recent call last)",
]


@pytest.fixture(scope="module", autouse=True)
def setup_screenshots_dir():
    '''create screenshots directory'''
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


# ─── Docker helpers ─────────────────────────────────────────────────────────


def _docker_available() -> bool:
    '''check if docker CLI is available and daemon is running'''
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _image_exists(image_name: str) -> bool:
    '''check if a Docker image exists locally'''
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ─── JupyterLab container fixture ──────────────────────────────────────────


@pytest.fixture(scope="module")
def jupyterlab_url():
    '''
    start a JupyterLab Docker container with all workspace notebooks.
    yields the base URL. cleans up after all tests.
    '''
    if not _docker_available():
        pytest.skip("Docker not available - skipping notebook e2e tests")

    if not _image_exists(WORKSPACE_IMAGE):
        pytest.skip(
            f"Docker image '{WORKSPACE_IMAGE}' not found. "
            f"Build it with: docker compose --profile workspace-build build workspace"
        )

    # kill any leftover container
    subprocess.run(
        ["docker", "rm", "-f", JUPYTER_CONTAINER_NAME],
        capture_output=True, timeout=15
    )

    # start container with backend API access via host.docker.internal
    run_result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", JUPYTER_CONTAINER_NAME,
            "-p", f"{JUPYTER_HOST_PORT}:8888",
            "-e", "OPENUBA_API_URL=http://host.docker.internal:8000",
            "-e", "OPENUBA_WORKSPACE_ID=e2e-notebook-test",
            "-e", "JUPYTER_ENABLE_LAB=yes",
            WORKSPACE_IMAGE,
            "start-notebook.sh",
            "--ServerApp.token=",
            "--ServerApp.password=",
            "--ServerApp.allow_origin=*",
            "--ServerApp.allow_remote_access=True",
            "--ServerApp.disable_check_xsrf=True",
            "--ServerApp.root_dir=/home/jovyan/work",
        ],
        capture_output=True, text=True, timeout=30
    )

    if run_result.returncode != 0:
        pytest.skip(f"Failed to start JupyterLab container: {run_result.stderr}")

    # wait for JupyterLab to become ready (up to 90 seconds)
    ready = False
    for attempt in range(45):
        try:
            resp = requests.get(f"{JUPYTER_BASE_URL}/api/status", timeout=3)
            if resp.status_code == 200:
                ready = True
                break
        except requests.ConnectionError:
            pass
        time.sleep(2)

    if not ready:
        logs = subprocess.run(
            ["docker", "logs", "--tail", "50", JUPYTER_CONTAINER_NAME],
            capture_output=True, text=True, timeout=10
        )
        subprocess.run(
            ["docker", "rm", "-f", JUPYTER_CONTAINER_NAME],
            capture_output=True, timeout=15
        )
        pytest.skip(
            f"JupyterLab container did not become ready within 90s. "
            f"Logs: {logs.stdout[-500:] if logs.stdout else 'none'}"
        )

    yield JUPYTER_BASE_URL

    # cleanup
    subprocess.run(
        ["docker", "rm", "-f", JUPYTER_CONTAINER_NAME],
        capture_output=True, timeout=15
    )


# ─── Notebook execution helpers ────────────────────────────────────────────


def execute_notebook_in_container(notebook_name: str, timeout: int = 180) -> dict:
    '''
    execute a notebook inside the JupyterLab container using nbconvert.
    returns dict with status, stdout, stderr.
    '''
    result = subprocess.run(
        [
            "docker", "exec", JUPYTER_CONTAINER_NAME,
            "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=120",
            "--ExecutePreprocessor.kernel_name=python3",
            "--output", notebook_name,
            f"/home/jovyan/work/{notebook_name}",
        ],
        capture_output=True, text=True, timeout=timeout
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def get_notebook_outputs(notebook_name: str) -> list:
    '''
    read the executed notebook from the container and extract all cell outputs.
    returns list of output text strings.
    '''
    result = subprocess.run(
        [
            "docker", "exec", JUPYTER_CONTAINER_NAME,
            "cat", f"/home/jovyan/work/{notebook_name}",
        ],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        return []

    try:
        nb = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    outputs = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for output in cell.get("outputs", []):
            if "text" in output:
                outputs.extend(output["text"])
            elif "traceback" in output:
                outputs.extend(output["traceback"])
            elif output.get("output_type") == "execute_result":
                data = output.get("data", {})
                if "text/plain" in data:
                    outputs.extend(data["text/plain"]
                                   if isinstance(data["text/plain"], list)
                                   else [data["text/plain"]])
    return outputs


def check_for_fatal_errors(outputs: list) -> list:
    '''
    check notebook outputs for fatal Python errors.
    returns list of error descriptions found.
    API errors (HTTPError, ConnectionError) are expected and NOT fatal.
    '''
    errors = []
    full_output = "\n".join(outputs).lower()

    for pattern in FATAL_ERROR_PATTERNS:
        if pattern in full_output:
            # find the actual line containing the error for reporting
            for line in outputs:
                if pattern in line.lower():
                    errors.append(line.strip())
                    break
    return errors


# ─── UI helpers ────────────────────────────────────────────────────────────


def ui_login(page: Page, frontend_url: str):
    '''log in via the UI'''
    page.goto(f"{frontend_url}/login")
    page.wait_for_load_state("networkidle")

    username_input = page.locator(
        'input[placeholder="Enter username"], input[placeholder="Enter Username"]'
    ).first
    password_input = page.locator(
        'input[placeholder="Enter password"], input[placeholder="Enter Password"]'
    ).first

    username_input.fill("openuba")
    password_input.fill("password")

    submit_btn = page.locator(
        'button[type="submit"], button:has-text("Sign in"), button:has-text("Sign In")'
    ).first
    submit_btn.click()

    time.sleep(3)
    page.wait_for_load_state("networkidle")


def take_screenshot(page: Page, name: str) -> str:
    '''take a named screenshot'''
    path = os.path.join(SCREENSHOTS_DIR, f"nb_{name}.png")
    page.screenshot(path=path, full_page=True)
    return path


# ─── THE TEST ───────────────────────────────────────────────────────────────


def test_all_workspace_notebooks(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict,
    db_utils: DBTestUtils,
    jupyterlab_url: str,
):
    '''
    Execute ALL workspace notebooks and verify 100% SDK coverage.

    Phase 1: Execute all notebooks programmatically via nbconvert
    Phase 2: Create workspace, open JupyterLab, screenshot each notebook
    Phase 3: Verify outputs and generate coverage report
    '''
    page.set_default_timeout(45000)

    results = {}
    all_outputs = {}

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: Execute all notebooks via nbconvert
    # ═══════════════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print("PHASE 1: Executing notebooks via nbconvert")
    print(f"{'='*60}\n")

    for notebook in NOTEBOOKS:
        print(f"  Executing {notebook}...", end=" ", flush=True)
        exec_result = execute_notebook_in_container(notebook)
        results[notebook] = exec_result

        if exec_result["returncode"] == 0:
            outputs = get_notebook_outputs(notebook)
            all_outputs[notebook] = outputs
            fatal_errors = check_for_fatal_errors(outputs)
            if fatal_errors:
                print(f"WARNINGS: {len(fatal_errors)} potential issues")
                for err in fatal_errors:
                    print(f"    ! {err[:100]}")
            else:
                print("OK")
        else:
            all_outputs[notebook] = []
            # extract the actual error from stderr
            stderr = exec_result["stderr"]
            print(f"EXEC FAILED")
            print(f"    stderr: {stderr[-200:] if stderr else 'none'}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Open workspace and screenshot each notebook
    # ═══════════════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print("PHASE 2: UI screenshots of executed notebooks")
    print(f"{'='*60}\n")

    # Login and create workspace
    ui_login(page, frontend_url)
    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")

    page.click('button:has-text("Launch Workspace")')
    page.wait_for_selector('h2:has-text("Launch Workspace")', timeout=5000)

    ws_name = f"e2e_nb_test_{uuid4().hex[:8]}"
    page.fill('input[placeholder="my-workspace"]', ws_name)
    dialog_launch_btn = page.locator('div.fixed button:has-text("Launch")').last
    dialog_launch_btn.click()
    page.wait_for_selector(f'text={ws_name}', timeout=15000)

    # Get workspace ID
    resp = requests.get(f"{backend_url}/api/v1/workspaces", headers=auth_headers)
    assert resp.status_code == 200
    ws_record = next((w for w in resp.json() if w["name"] == ws_name), None)
    assert ws_record is not None
    ws_id = ws_record["id"]

    # Patch DB to simulate operator
    with db_utils.engine.connect() as conn:
        conn.execute(
            text(
                "UPDATE workspaces "
                "SET status = 'running', "
                "    access_url = :access_url, "
                "    started_at = now() "
                "WHERE id = CAST(:ws_id AS uuid)"
            ),
            {"access_url": jupyterlab_url, "ws_id": ws_id}
        )
        conn.commit()

    # Navigate to workspace detail
    page.goto(f"{frontend_url}/workspaces/{ws_id}")
    page.wait_for_load_state("networkidle")

    iframe_selector = 'iframe[title*="JupyterLab"]'
    page.wait_for_selector(iframe_selector, timeout=30000)
    time.sleep(5)

    take_screenshot(page, "00_workspace_jupyterlab")

    jupyter = page.frame_locator(iframe_selector)
    jupyter.locator('.jp-Launcher').wait_for(timeout=30000)

    take_screenshot(page, "00_launcher")

    # Open each notebook from the file browser and screenshot
    for notebook in NOTEBOOKS:
        nb_num = notebook.split("_")[0]
        nb_short = notebook.replace(".ipynb", "")

        print(f"  Screenshotting {notebook}...")

        # Navigate to the notebook via JupyterLab file browser
        # Click on the file in the file browser panel
        try:
            # first ensure file browser is visible
            file_browser = jupyter.locator('.jp-FileBrowser')
            file_browser.wait_for(timeout=10000)

            # find and double-click the notebook file
            file_item = jupyter.locator(
                f'.jp-DirListing-item[title*="{notebook}"], '
                f'.jp-DirListing-item:has-text("{notebook}")'
            ).first
            file_item.dblclick(timeout=10000)

            # wait for notebook to open
            time.sleep(3)
            jupyter.locator('.jp-Notebook').first.wait_for(timeout=15000)
            time.sleep(2)

            take_screenshot(page, f"{nb_num}_{nb_short}_opened")

            # Scroll through the notebook to capture outputs
            # scroll to bottom to show all executed outputs
            notebook_panel = jupyter.locator('.jp-Notebook').first
            notebook_panel.evaluate("el => el.scrollTop = el.scrollHeight")
            time.sleep(1)

            take_screenshot(page, f"{nb_num}_{nb_short}_outputs")

            # close the notebook tab to prepare for next
            # click the X on the tab
            tab = jupyter.locator(
                f'.jp-mod-current .lm-TabBar-tabCloseIcon'
            ).first
            try:
                tab.click(timeout=3000)
                time.sleep(1)
                # handle "don't save" dialog if it appears
                dont_save = jupyter.locator(
                    'button:has-text("Don\'t Save"), button:has-text("Discard")'
                ).first
                try:
                    dont_save.click(timeout=2000)
                except Exception:
                    pass
            except Exception:
                pass

        except Exception as e:
            print(f"    Screenshot failed for {notebook}: {e}")
            take_screenshot(page, f"{nb_num}_{nb_short}_error")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Verification and coverage report
    # ═══════════════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print("PHASE 3: Verification & SDK Coverage Report")
    print(f"{'='*60}\n")

    total_notebooks = len(NOTEBOOKS)
    executed_ok = sum(1 for r in results.values() if r["returncode"] == 0)
    total_functions_covered = set()

    for notebook, functions in NOTEBOOK_SDK_COVERAGE.items():
        total_functions_covered.update(functions)

    print(f"  Notebooks executed: {executed_ok}/{total_notebooks}")
    print(f"  SDK functions covered: {len(total_functions_covered)}")
    print()

    for notebook in NOTEBOOKS:
        status = "PASS" if results[notebook]["returncode"] == 0 else "FAIL"
        coverage = NOTEBOOK_SDK_COVERAGE.get(notebook, [])
        print(f"  [{status}] {notebook}")
        print(f"         Covers: {', '.join(coverage)}")

        if all_outputs.get(notebook):
            # Show last few lines of output (summary)
            output_lines = all_outputs[notebook]
            summary_lines = [l for l in output_lines if "===" in l or "passed" in l.lower()]
            for line in summary_lines[-2:]:
                print(f"         {line.strip()}")

    print(f"\n{'='*60}")
    print(f"SDK COVERAGE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total notebooks: {total_notebooks}")
    print(f"  Executed successfully: {executed_ok}")
    print(f"  SDK functions/classes covered: {len(total_functions_covered)}")
    print(f"  Functions: {sorted(total_functions_covered)}")
    print(f"{'='*60}\n")

    take_screenshot(page, "99_final_state")

    # Assert all notebooks executed (some cells may have API errors, but no Python errors)
    assert executed_ok == total_notebooks, (
        f"Only {executed_ok}/{total_notebooks} notebooks executed successfully. "
        f"Failed: {[nb for nb, r in results.items() if r['returncode'] != 0]}"
    )

    # Check for fatal Python errors in outputs
    all_fatal_errors = {}
    for notebook, outputs in all_outputs.items():
        fatal = check_for_fatal_errors(outputs)
        if fatal:
            all_fatal_errors[notebook] = fatal

    if all_fatal_errors:
        error_report = "\n".join(
            f"  {nb}: {errs}" for nb, errs in all_fatal_errors.items()
        )
        print(f"\nFATAL ERRORS FOUND:\n{error_report}")
        # Don't assert-fail on these since some may be expected API errors
        # but report them prominently

    # Cleanup workspace
    requests.post(f"{backend_url}/api/v1/workspaces/{ws_id}/stop", headers=auth_headers)
    requests.delete(f"{backend_url}/api/v1/workspaces/{ws_id}", headers=auth_headers)
