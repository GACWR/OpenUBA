'''
Copyright 2019-Present The OpenUBA Platform Authors
model-runner SSRF guard tests (#145)

the runner (docker/model-runner/runner.py) ships its own inlined copy of the
SSRF guard because that container does not import `core`. this test loads the
runner module directly and exercises `_assert_safe_url` so the two guard copies
(core.integrations.splunk vs runner) cannot silently drift.
'''

import socket
import importlib.util
from pathlib import Path

import pytest

_RUNNER_PATH = Path(__file__).resolve().parents[3] / "docker" / "model-runner" / "runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("openuba_runner_under_test", _RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


runner = _load_runner()


def test_runner_blocks_link_local_metadata():
    with pytest.raises(ValueError):
        runner._assert_safe_url("http://169.254.169.254/latest/meta-data/")


def test_runner_blocks_non_http_scheme():
    with pytest.raises(ValueError):
        runner._assert_safe_url("file:///etc/passwd")


def test_runner_blocks_ipv4_mapped_ipv6(monkeypatch):
    # the runner guard must unwrap ::ffff:169.254.169.254 just like the core one
    monkeypatch.setattr(
        socket, "getaddrinfo",
        lambda host, port, *a, **k: [(10, 1, 6, "", ("::ffff:169.254.169.254", port or 0, 0, 0))],
    )
    with pytest.raises(ValueError):
        runner._assert_safe_url("https://evil.example.com:8088/x")


def test_runner_allows_internal_private_host():
    # numeric private IP resolves without DNS → not link-local → allowed
    runner._assert_safe_url("https://10.0.0.5:8088/services/search/jobs/export")


def test_runner_fail_open_on_unresolvable():
    # an unresolvable host is let through (best-effort; the request fails anyway)
    runner._assert_safe_url("https://splunk.invalid.nonexistent:8089/x")


# ─── splunk query build: index scoping (#145) ───────────────────────────────

def test_build_splunk_query_scopes_index():
    assert runner._build_splunk_query("sourcetype=access", "proxy") == "search index=proxy sourcetype=access"

def test_build_splunk_query_respects_existing_index():
    assert runner._build_splunk_query("search index=main foo", "proxy") == "search index=main foo"

def test_build_splunk_query_leaves_generating_command():
    assert runner._build_splunk_query("| tstats count", "proxy") == "| tstats count"

def test_build_splunk_query_no_index():
    assert runner._build_splunk_query("foo=bar") == "search foo=bar"
