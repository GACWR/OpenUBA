'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e test: workspace -> JupyterLab iframe -> create notebook -> import openuba -> execute cells

This is THE fundamental test proving the workspace experience works end-to-end:
1. Create a workspace in the UI
2. JupyterLab loads in the embedded iframe
3. Create a new Python notebook
4. import openuba and use the SDK
5. Screenshots at every step
'''

import os
import time
import subprocess
import pytest
import requests
from uuid import uuid4
from playwright.sync_api import Page
from sqlalchemy import text

from core.tests.e2e.db_utils import DBTestUtils

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
JUPYTER_HOST_PORT = 38888
JUPYTER_CONTAINER_NAME = "e2e-test-jupyterlab"
WORKSPACE_IMAGE = "openuba-workspace:latest"
JUPYTER_BASE_URL = f"http://localhost:{JUPYTER_HOST_PORT}"


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
    start a JupyterLab Docker container from the openuba-workspace image.
    yields the base URL (http://localhost:38888).
    cleans up the container after all tests in this module.

    skips the entire module if Docker is unavailable or the image is missing.
    '''
    if not _docker_available():
        pytest.skip("Docker not available - skipping JupyterLab e2e tests")

    if not _image_exists(WORKSPACE_IMAGE):
        pytest.skip(
            f"Docker image '{WORKSPACE_IMAGE}' not found. "
            f"Build it with: docker compose --profile workspace-build build workspace"
        )

    # kill any leftover container from a previous failed run
    subprocess.run(
        ["docker", "rm", "-f", JUPYTER_CONTAINER_NAME],
        capture_output=True, timeout=15
    )

    # start the container with explicit token-less config via command line
    # (ensures token-less access even if the image config isn't applied correctly)
    run_result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", JUPYTER_CONTAINER_NAME,
            "-p", f"{JUPYTER_HOST_PORT}:8888",
            "-e", "OPENUBA_API_URL=http://host.docker.internal:8000",
            "-e", "OPENUBA_WORKSPACE_ID=e2e-test",
            "-e", "JUPYTER_ENABLE_LAB=yes",
            WORKSPACE_IMAGE,
            "start-notebook.sh",
            "--ServerApp.token=",
            "--ServerApp.password=",
            "--ServerApp.allow_origin=*",
            "--ServerApp.allow_remote_access=True",
            "--ServerApp.disable_check_xsrf=True",
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
        # grab container logs for debugging
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


# ─── Helpers ────────────────────────────────────────────────────────────────


def ui_login(page: Page, frontend_url: str):
    '''log in via the UI — handles both deployed and local frontend variants'''
    page.goto(f"{frontend_url}/login")
    page.wait_for_load_state("networkidle")

    # try standard placeholder first, fall back to alternate
    username_input = page.locator(
        'input[placeholder="Enter username"], input[placeholder="Enter Username"]'
    ).first
    password_input = page.locator(
        'input[placeholder="Enter password"], input[placeholder="Enter Password"]'
    ).first

    username_input.fill("openuba")
    password_input.fill("password")

    # click submit button — handle both "Sign in" and standard submit
    submit_btn = page.locator(
        'button[type="submit"], button:has-text("Sign in"), button:has-text("Sign In")'
    ).first
    submit_btn.click()

    # wait for navigation away from login (flexible — could go to / or /workspaces etc)
    time.sleep(3)
    page.wait_for_load_state("networkidle")


def take_screenshot(page: Page, step: int, name: str) -> str:
    '''take a numbered screenshot for clear step-by-step progression'''
    filename = f"ws_jupyter_{step:02d}_{name}.png"
    path = os.path.join(SCREENSHOTS_DIR, filename)
    page.screenshot(path=path, full_page=True)
    return path


def type_in_jupyter_cell(frame_locator, cell_locator, code: str):
    '''
    type code into a JupyterLab cell, handling CodeMirror 6 quirks.
    uses keyboard typing for reliable CodeMirror 6 interaction.
    '''
    editor = cell_locator.locator('.cm-content[contenteditable="true"]')
    editor.click()
    # select all and delete any existing content
    editor.press("Control+a")
    editor.press("Backspace")
    time.sleep(0.3)

    # type each line with Enter between them
    for line_idx, line in enumerate(code.split("\n")):
        if line_idx > 0:
            editor.press("Enter")
        editor.type(line, delay=20)


# ─── THE TEST ───────────────────────────────────────────────────────────────


def test_workspace_jupyterlab_sdk_flow(
    page: Page,
    frontend_url: str,
    backend_url: str,
    auth_headers: dict,
    db_utils: DBTestUtils,
    jupyterlab_url: str,
):
    '''
    FULL end-to-end workspace test with screenshots at every step:

    1. Navigate to workspaces page
    2. Create workspace via the Launch Workspace UI dialog
    3. Patch DB to simulate operator (status=running, access_url=container)
    4. Navigate to workspace detail page, wait for JupyterLab iframe
    5. Inside iframe: create Python notebook
    6. Type 'import openuba' and execute
    7. Type SDK version check and execute
    8. Type SDK method listing and execute
    9. Verify outputs, take final screenshot
    '''

    step = 0

    # increase default timeout for iframe interactions
    page.set_default_timeout(45000)

    # ─── Step 1: Login and navigate to workspaces ──────────────────

    ui_login(page, frontend_url)

    page.goto(f"{frontend_url}/workspaces")
    page.wait_for_load_state("networkidle")

    step += 1
    take_screenshot(page, step, "workspaces_page")

    # ─── Step 2: Open launch dialog and create workspace ───────────

    page.click('button:has-text("Launch Workspace")')
    page.wait_for_selector('h2:has-text("Launch Workspace")', timeout=5000)

    ws_name = f"e2e_test_ws_jupyter_{uuid4().hex[:8]}"
    page.fill('input[placeholder="my-workspace"]', ws_name)

    step += 1
    take_screenshot(page, step, "launch_dialog")

    # click the Launch button inside the dialog (not the header button)
    dialog_launch_btn = page.locator(
        'div.fixed button:has-text("Launch")'
    ).last
    dialog_launch_btn.click()

    # wait for dialog to close and workspace to appear in the list
    page.wait_for_selector(f'text={ws_name}', timeout=15000)

    step += 1
    take_screenshot(page, step, "workspace_created")

    # ─── Step 3: Get workspace ID from API ─────────────────────────

    resp = requests.get(
        f"{backend_url}/api/v1/workspaces",
        headers=auth_headers
    )
    assert resp.status_code == 200
    workspaces = resp.json()
    ws_record = next((w for w in workspaces if w["name"] == ws_name), None)
    assert ws_record is not None, f"Workspace '{ws_name}' not found in API response"
    ws_id = ws_record["id"]

    # ─── Step 4: Patch DB to simulate K8s operator ─────────────────
    # In production, the K8s operator provisions a JupyterLab pod and
    # updates the workspace to status=running with access_url.
    # Since we don't have K8s in e2e, we patch the DB to point at
    # our Docker container running JupyterLab.

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

    # ─── Step 5: Navigate to workspace detail page ─────────────────

    page.goto(f"{frontend_url}/workspaces/{ws_id}")
    page.wait_for_load_state("networkidle")

    step += 1
    take_screenshot(page, step, "workspace_detail_loading")

    # the frontend will poll status (3s), see running, then probe access_url (2s)
    # since our JupyterLab container is up, the probe succeeds and iframe renders
    iframe_selector = 'iframe[title*="JupyterLab"]'
    page.wait_for_selector(iframe_selector, timeout=30000)

    step += 1
    take_screenshot(page, step, "workspace_detail_running")

    # give iframe content time to fully load
    time.sleep(5)

    step += 1
    take_screenshot(page, step, "jupyterlab_iframe_loaded")

    # ─── Step 6: Interact with JupyterLab in the iframe ────────────

    jupyter = page.frame_locator(iframe_selector)

    # wait for JupyterLab launcher to appear
    jupyter.locator('.jp-Launcher').wait_for(timeout=30000)

    step += 1
    take_screenshot(page, step, "jupyterlab_launcher")

    # ─── Step 7: Create a new Python notebook ──────────────────────

    # click on the Python 3 notebook card in the launcher
    notebook_card = jupyter.locator(
        '.jp-LauncherCard[title*="Python"], '
        '.jp-LauncherCard:has-text("Python 3")'
    ).first
    notebook_card.click()

    # wait for the notebook to open (notebook widget + first cell)
    jupyter.locator('.jp-Notebook').wait_for(timeout=20000)
    jupyter.locator('.jp-Cell').first.wait_for(timeout=15000)

    # wait a bit for the kernel to be ready
    time.sleep(3)

    step += 1
    take_screenshot(page, step, "new_notebook_created")

    # ─── Step 8: Type and execute 'import openuba' ─────────────────

    first_cell = jupyter.locator('.jp-Cell').first
    type_in_jupyter_cell(
        jupyter, first_cell,
        "import openuba\nprint(f'OpenUBA SDK v{openuba.__version__} loaded successfully!')"
    )

    step += 1
    take_screenshot(page, step, "import_openuba_typed")

    # execute with Shift+Enter
    first_cell.locator('.cm-content[contenteditable="true"]').press("Shift+Enter")

    # wait for cell output to appear
    time.sleep(5)

    step += 1
    take_screenshot(page, step, "import_openuba_executed")

    # ─── Step 9: Type and execute SDK version check ────────────────

    time.sleep(1)
    second_cell = jupyter.locator('.jp-Cell').last
    type_in_jupyter_cell(
        jupyter, second_cell,
        "# Check SDK version and available functions\n"
        "print(f'Version: {openuba.__version__}')\n"
        "print(f'Client: {openuba.OpenUBAClient.__name__}')\n"
        "print(f'Functions: {len(openuba.__all__)} exported')"
    )

    step += 1
    take_screenshot(page, step, "version_check_typed")

    second_cell.locator('.cm-content[contenteditable="true"]').press("Shift+Enter")
    time.sleep(5)

    step += 1
    take_screenshot(page, step, "version_check_executed")

    # ─── Step 10: Type and execute SDK method listing ──────────────

    time.sleep(1)
    third_cell = jupyter.locator('.jp-Cell').last
    type_in_jupyter_cell(
        jupyter, third_cell,
        "# List available SDK operations\n"
        "sdk_methods = [m for m in openuba.__all__ if not m.startswith('_')]\n"
        "print('Available SDK operations:')\n"
        "for method in sdk_methods[:15]:\n"
        "    print(f'  - openuba.{method}()')"
    )

    step += 1
    take_screenshot(page, step, "sdk_methods_typed")

    third_cell.locator('.cm-content[contenteditable="true"]').press("Shift+Enter")
    time.sleep(5)

    step += 1
    take_screenshot(page, step, "sdk_methods_executed")

    # ─── Step 11: Verify outputs and take final screenshot ─────────

    # collect all output text from the notebook
    all_outputs = jupyter.locator('.jp-OutputArea-output').all_text_contents()
    output_text = " ".join(all_outputs).lower()

    # verify import succeeded (no ImportError/ModuleNotFoundError)
    assert "modulenotfounderror" not in output_text, \
        f"import openuba failed inside JupyterLab: {output_text}"
    assert "importerror" not in output_text, \
        f"ImportError in JupyterLab: {output_text}"

    # verify SDK version was printed
    assert "0.1.0" in output_text, \
        f"Expected SDK version '0.1.0' in output, got: {output_text}"

    # verify SDK methods were listed
    assert "configure" in output_text, \
        f"Expected 'configure' in SDK method listing, got: {output_text}"

    step += 1
    take_screenshot(page, step, "final_notebook")

    print(f"\n{'='*60}")
    print(f"WORKSPACE JUPYTERLAB SDK TEST PASSED")
    print(f"  Workspace: {ws_name}")
    print(f"  JupyterLab URL: {jupyterlab_url}")
    print(f"  Screenshots: {step} taken in {SCREENSHOTS_DIR}/ws_jupyter_*.png")
    print(f"{'='*60}\n")

    # ─── Step 12: Cleanup ──────────────────────────────────────────

    requests.post(
        f"{backend_url}/api/v1/workspaces/{ws_id}/stop",
        headers=auth_headers
    )
    requests.delete(
        f"{backend_url}/api/v1/workspaces/{ws_id}",
        headers=auth_headers
    )
