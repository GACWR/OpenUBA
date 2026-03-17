'''
Copyright 2019-Present The OpenUBA Platform Authors
e2e test: workspace lifecycle with JupyterLab interaction

Proves the full flow with the REAL K8s operator:
  1. Login -> navigate to /workspaces
  2. Launch a workspace via the UI dialog
  3. Wait for the K8s operator to provision the pod (status=running)
  4. Open workspace detail page -> JupyterLab loads in iframe
  5. Create a new Python notebook inside JupyterLab
  6. Execute hello world code in the notebook
  7. Import and use the openuba SDK
  8. Screenshots at every step
'''

import os
import time
import pytest
import requests
from uuid import uuid4
from playwright.sync_api import Page

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BACKEND_URL = os.getenv("E2E_BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("E2E_FRONTEND_URL", "http://localhost:3000")


# ─── Helpers ────────────────────────────────────────────────────────────────


def _screenshot(page: Page, step: int, name: str):
    '''save a numbered screenshot'''
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOTS_DIR, f"ws_jupyter_{step:02d}_{name}.png")
    page.screenshot(path=path, full_page=True)


def _login(page: Page):
    '''login via the UI'''
    page.goto(f"{FRONTEND_URL}/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[placeholder="Enter username"]', "openuba")
    page.fill('input[placeholder="Enter password"]', "password")
    page.click('button[type="submit"]')
    page.wait_for_url("**/", timeout=15000)
    page.wait_for_load_state("networkidle")


def _get_auth_headers() -> dict:
    '''get auth headers via API'''
    resp = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={"username": "openuba", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _wait_for_workspace_running(workspace_id: str, headers: dict, timeout: int = 120) -> dict:
    '''poll workspace API until status is running'''
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{BACKEND_URL}/api/v1/workspaces/{workspace_id}",
            headers=headers,
        )
        if resp.status_code == 200:
            ws = resp.json()
            if ws["status"] == "running":
                return ws
            if ws["status"] == "failed":
                pytest.fail(f"workspace reached failed status: {ws}")
        time.sleep(3)
    pytest.fail(f"workspace {workspace_id} did not reach running within {timeout}s")


def _cleanup_workspace(workspace_id: str, headers: dict):
    '''stop and delete workspace via API + K8s CRD'''
    try:
        requests.post(f"{BACKEND_URL}/api/v1/workspaces/{workspace_id}/stop", headers=headers)
    except Exception:
        pass
    try:
        requests.delete(f"{BACKEND_URL}/api/v1/workspaces/{workspace_id}", headers=headers)
    except Exception:
        pass
    # also delete the K8s CRD to free nodeport and trigger resource cleanup
    cr_name = f"uba-ws-{workspace_id[:8]}"
    try:
        import subprocess
        subprocess.run(
            ["kubectl", "delete", "ubaworkspace", cr_name, "-n", "openuba"],
            capture_output=True, timeout=15,
        )
    except Exception:
        pass


def _type_in_cell(frame_locator, cell, code: str):
    '''type code into a JupyterLab cell (CodeMirror 6)'''
    editor = cell.locator('.cm-content[contenteditable="true"]')
    editor.click()
    editor.press("Control+a")
    editor.press("Backspace")
    time.sleep(0.3)
    for i, line in enumerate(code.split("\n")):
        if i > 0:
            editor.press("Enter")
        editor.type(line, delay=20)


# ─── THE TEST ───────────────────────────────────────────────────────────────


def test_workspace_jupyterlab_hello_world(page: Page):
    '''
    full e2e test: launch workspace from UI, K8s operator provisions pod,
    JupyterLab loads in iframe, create notebook, run hello world + SDK import
    '''
    ws_name = f"e2e_test_ws_{uuid4().hex[:8]}"
    headers = _get_auth_headers()
    workspace_id = None
    step = 0

    page.set_default_timeout(45000)

    try:
        # ── Step 1: Login ──────────────────────────────────────────────
        _login(page)
        step += 1
        _screenshot(page, step, "logged_in")

        # ── Step 2: Navigate to /workspaces ────────────────────────────
        page.goto(f"{FRONTEND_URL}/workspaces")
        page.wait_for_load_state("networkidle")
        step += 1
        _screenshot(page, step, "workspaces_page")

        # ── Step 3: Open Launch Workspace dialog ───────────────────────
        page.click('button:has-text("Launch Workspace")')
        page.wait_for_selector('h2:has-text("Launch Workspace")', timeout=5000)
        step += 1
        _screenshot(page, step, "launch_dialog_open")

        # ── Step 4: Fill dialog and launch ─────────────────────────────
        page.fill('input[placeholder="my-workspace"]', ws_name)
        step += 1
        _screenshot(page, step, "dialog_filled")

        # click the Launch button inside the dialog
        page.locator('div.fixed button:has-text("Launch")').last.click()

        # wait for dialog to close and workspace to appear
        page.wait_for_selector('input[placeholder="my-workspace"]', state="detached", timeout=15000)
        page.wait_for_load_state("networkidle")
        step += 1
        _screenshot(page, step, "workspace_created")

        # ── Step 5: Get workspace ID from API ─────────────────────────
        resp = requests.get(f"{BACKEND_URL}/api/v1/workspaces", headers=headers)
        assert resp.status_code == 200
        ws_match = [w for w in resp.json() if w["name"] == ws_name]
        assert len(ws_match) == 1, f"expected 1 workspace named {ws_name}, found {len(ws_match)}"
        workspace_id = ws_match[0]["id"]

        # ── Step 6: Wait for K8s operator to make workspace running ───
        print(f"  waiting for workspace {workspace_id} to reach running...")
        ws_data = _wait_for_workspace_running(workspace_id, headers, timeout=120)
        assert ws_data["access_url"] is not None
        print(f"  workspace running at {ws_data['access_url']}")
        step += 1
        _screenshot(page, step, "workspace_running_confirmed")

        # ── Step 7: Navigate to workspace detail page ─────────────────
        page.goto(f"{FRONTEND_URL}/workspaces/{workspace_id}")
        page.wait_for_load_state("networkidle")
        step += 1
        _screenshot(page, step, "workspace_detail")

        # ── Step 8: Wait for JupyterLab iframe ────────────────────────
        # The frontend probes access_url then renders iframe
        iframe_sel = 'iframe[title*="JupyterLab"]'
        page.wait_for_selector(iframe_sel, timeout=90000)
        step += 1
        _screenshot(page, step, "iframe_visible")

        # give iframe time to fully render
        time.sleep(5)

        # ── Step 9: Interact with JupyterLab in iframe ───────────────
        jupyter = page.frame_locator(iframe_sel)
        jupyter.locator('.jp-Launcher').wait_for(timeout=60000)
        step += 1
        _screenshot(page, step, "jupyterlab_launcher")

        # ── Step 10: Create new Python notebook ───────────────────────
        python_card = jupyter.locator(
            '.jp-LauncherCard[title*="Python"], '
            '.jp-LauncherCard:has-text("Python 3")'
        ).first
        python_card.click()

        jupyter.locator('.jp-Notebook').wait_for(timeout=30000)
        jupyter.locator('.jp-Cell').first.wait_for(timeout=15000)
        time.sleep(3)
        step += 1
        _screenshot(page, step, "new_notebook")

        # ── Step 11: Type and execute hello world ─────────────────────
        cell1 = jupyter.locator('.jp-Cell').first
        _type_in_cell(jupyter, cell1, 'print("hello world from OpenUBA workspace!")')
        step += 1
        _screenshot(page, step, "hello_world_typed")

        cell1.locator('.cm-content[contenteditable="true"]').press("Shift+Enter")
        time.sleep(5)
        step += 1
        _screenshot(page, step, "hello_world_executed")

        # verify hello world output
        outputs = jupyter.locator('.jp-OutputArea-output')
        output1 = outputs.first.inner_text(timeout=15000)
        assert "hello world from OpenUBA workspace!" in output1, \
            f"expected hello world output, got: {output1}"

        # ── Step 12: Import and use openuba SDK ───────────────────────
        time.sleep(2)
        cell2 = jupyter.locator('.jp-Cell').last
        _type_in_cell(jupyter, cell2,
                       'import openuba\n'
                       'print(f"openuba SDK v{openuba.__version__}")')
        step += 1
        _screenshot(page, step, "sdk_import_typed")

        cell2.locator('.cm-content[contenteditable="true"]').press("Shift+Enter")
        time.sleep(5)
        step += 1
        _screenshot(page, step, "sdk_import_executed")

        # verify no import errors
        all_outputs = jupyter.locator('.jp-OutputArea-output').all_text_contents()
        output_text = " ".join(all_outputs).lower()
        assert "modulenotfounderror" not in output_text, \
            f"openuba import failed: {output_text}"
        assert "error" not in output_text, \
            f"unexpected error in output: {output_text}"

        step += 1
        _screenshot(page, step, "final")

        print(f"\n{'='*60}")
        print(f"WORKSPACE JUPYTERLAB HELLO WORLD TEST PASSED")
        print(f"  Workspace: {ws_name} ({workspace_id})")
        print(f"  Screenshots: {step} taken in {SCREENSHOTS_DIR}/")
        print(f"{'='*60}\n")

    finally:
        if workspace_id:
            _cleanup_workspace(workspace_id, headers)
