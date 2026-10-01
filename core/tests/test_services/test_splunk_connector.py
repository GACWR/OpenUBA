'''
Copyright 2019-Present The OpenUBA Platform Authors
splunk connector tests (issue #99)

dedicated subsuite for the Splunk integration. All network calls are mocked
(no live Splunk), so these run in the standard unit test job. Covers query
normalization, search parsing + auth, HEC output, and connectivity probing.

Lives under test_services/ (not test_integrations/) so it is included by the
CI unit filter `-k "not e2e and not integration"`.
'''

import json
from unittest.mock import MagicMock, patch

import pytest

from core.integrations import splunk as splunk_mod
from core.integrations.splunk import SplunkConnector


def _resp(status=200, text="", json_body=None):
    r = MagicMock()
    r.status_code = status
    r.text = text
    if json_body is not None:
        r.json.return_value = json_body
    return r


# ─── query normalization ─────────────────────────────────────────────────────

def test_normalize_query_prepends_search():
    assert SplunkConnector._normalize_query("index=main error") == "search index=main error"


def test_normalize_query_leaves_search_prefixed():
    assert SplunkConnector._normalize_query("search index=main") == "search index=main"


def test_normalize_query_leaves_generating_command():
    assert SplunkConnector._normalize_query("| tstats count") == "| tstats count"


def test_normalize_query_rejects_empty():
    with pytest.raises(ValueError):
        SplunkConnector._normalize_query("   ")


# ─── config ──────────────────────────────────────────────────────────────────

def test_env_fallback(monkeypatch):
    monkeypatch.setenv("SPLUNK_HOST", "https://splunk:8089/")
    monkeypatch.setenv("SPLUNK_TOKEN", "tok")
    monkeypatch.setenv("SPLUNK_HEC_URL", "https://splunk:8088/")
    monkeypatch.setenv("SPLUNK_HEC_TOKEN", "hectok")
    c = SplunkConnector()
    assert c.host == "https://splunk:8089"      # trailing slash stripped
    assert c.token == "tok"
    assert c.hec_url == "https://splunk:8088"
    assert c.hec_token == "hectok"


def test_from_config():
    c = SplunkConnector.from_config({
        "host": "https://s:8089", "username": "admin", "password": "pw",
        "verify_ssl": False,
    })
    assert c.host == "https://s:8089"
    assert c.username == "admin"
    assert c.verify_ssl is False


# ─── search (input) ──────────────────────────────────────────────────────────

def test_search_parses_ndjson_and_uses_bearer():
    ndjson = "\n".join([
        json.dumps({"preview": False, "offset": 0, "result": {"user": "alice", "count": "3"}}),
        json.dumps({"result": {"user": "bob", "count": "7"}}),
        json.dumps({"lastrow": True}),  # non-result line ignored
        "",  # blank line ignored
    ])
    c = SplunkConnector(host="https://splunk:8089", token="tok")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(200, ndjson)
        rows = c.search("index=main", max_count=500)

    assert rows == [{"user": "alice", "count": "3"}, {"user": "bob", "count": "7"}]
    args, kwargs = req.post.call_args
    assert args[0] == "https://splunk:8089/services/search/jobs/export"
    assert kwargs["data"]["search"] == "search index=main"
    assert kwargs["data"]["count"] == 500
    assert kwargs["headers"]["Authorization"] == "Bearer tok"
    assert kwargs["auth"] is None


def test_search_uses_basic_auth_without_token():
    c = SplunkConnector(host="https://splunk:8089", username="admin", password="pw")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(200, "")
        c.search("index=main")
    _, kwargs = req.post.call_args
    assert "Authorization" not in kwargs["headers"]
    assert kwargs["auth"] == ("admin", "pw")


def test_search_raises_on_error_status():
    c = SplunkConnector(host="https://splunk:8089", token="t")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(401, "unauthorized")
        with pytest.raises(ValueError, match="401"):
            c.search("index=main")


def test_search_requires_host():
    with pytest.raises(ValueError, match="host not configured"):
        SplunkConnector(host="").search("index=main")


# ─── HEC output ──────────────────────────────────────────────────────────────

def test_send_event_posts_to_hec_with_auth():
    c = SplunkConnector(hec_url="https://splunk:8088", hec_token="hectok")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(200)
        ok = c.send_event({"a": 1}, sourcetype="openuba", index="main")

    assert ok is True
    args, kwargs = req.post.call_args
    assert args[0] == "https://splunk:8088/services/collector/event"
    assert kwargs["headers"]["Authorization"] == "Splunk hectok"
    body = json.loads(kwargs["data"])
    assert body["event"] == {"a": 1}
    assert body["index"] == "main"
    assert body["sourcetype"] == "openuba"


def test_send_event_returns_false_when_hec_unconfigured():
    c = SplunkConnector()
    assert c.send_event({"a": 1}) is False


def test_send_event_returns_false_on_error_status():
    c = SplunkConnector(hec_url="https://splunk:8088", hec_token="t")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(403, "forbidden")
        assert c.send_event({"a": 1}) is False


def test_send_anomaly_uses_anomaly_sourcetype():
    c = SplunkConnector(hec_url="https://splunk:8088", hec_token="t")
    with patch.object(splunk_mod, "requests") as req:
        req.post.return_value = _resp(200)
        c.send_anomaly({"entity_id": "u1", "risk_score": 0.9})
    _, kwargs = req.post.call_args
    assert json.loads(kwargs["data"])["sourcetype"] == "openuba:anomaly"


def test_send_anomalies_counts_successes():
    c = SplunkConnector(hec_url="https://splunk:8088", hec_token="t")
    with patch.object(splunk_mod, "requests") as req:
        req.post.side_effect = [_resp(200), _resp(500, "err"), _resp(200)]
        sent = c.send_anomalies([{"a": 1}, {"a": 2}, {"a": 3}])
    assert sent == 2


# ─── connectivity ────────────────────────────────────────────────────────────

def test_test_connection_ok():
    c = SplunkConnector(host="https://splunk:8089", token="t")
    body = {"entry": [{"content": {"version": "9.2.1"}}]}
    with patch.object(splunk_mod, "requests") as req:
        req.get.return_value = _resp(200, json_body=body)
        result = c.test_connection()
    assert result == {"status": "connected", "version": "9.2.1"}


def test_test_connection_error_status():
    c = SplunkConnector(host="https://splunk:8089", token="t")
    with patch.object(splunk_mod, "requests") as req:
        req.get.return_value = _resp(500)
        result = c.test_connection()
    assert result["status"] == "error"


def test_test_connection_unconfigured():
    result = SplunkConnector().test_connection()
    assert result["status"] == "error"


# ─── SSRF guard (#145) ───────────────────────────────────────────────────────

def test_assert_safe_endpoint_rejects_non_http_scheme():
    with pytest.raises(ValueError):
        splunk_mod._assert_safe_endpoint("file:///etc/passwd")
    with pytest.raises(ValueError):
        splunk_mod._assert_safe_endpoint("gopher://splunk:8088/x")


def test_assert_safe_endpoint_rejects_link_local_metadata():
    # cloud instance-metadata endpoint — the classic SSRF exfil target
    with pytest.raises(ValueError):
        splunk_mod._assert_safe_endpoint("http://169.254.169.254/latest/meta-data/")


def test_assert_safe_endpoint_allows_internal_private_host():
    # internal/private Splunk is the normal deployment — must NOT be blocked.
    # numeric IPs resolve without DNS, so this is deterministic offline.
    splunk_mod._assert_safe_endpoint("https://10.0.0.5:8088/services/collector/event")
    splunk_mod._assert_safe_endpoint("https://127.0.0.1:8088/services/collector/event")


def test_send_event_refuses_link_local_target():
    # a hec_url pointed at instance metadata must be refused (returns False,
    # never fires the request)
    c = SplunkConnector(hec_url="http://169.254.169.254", hec_token="t")
    with patch("core.integrations.splunk.requests.post") as post:
        assert c.send_event({"entity_id": "u1"}) is False
        post.assert_not_called()


def test_search_refuses_link_local_host():
    c = SplunkConnector(host="http://169.254.169.254:8089", token="t")
    with patch("core.integrations.splunk.requests.post") as post:
        with pytest.raises(ValueError):
            c.search("index=main")
        post.assert_not_called()


# ─── SSRF guard: resolved-address bypasses (#145 adversarial follow-up) ──────

def test_assert_safe_endpoint_rejects_ipv4_mapped_ipv6(monkeypatch):
    # a hostname resolving to ::ffff:169.254.169.254 must still be blocked
    # (is_link_local is False on the mapped form unless we unwrap it)
    monkeypatch.setattr(
        splunk_mod.socket, "getaddrinfo",
        lambda host, port, *a, **k: [(10, 1, 6, "", ("::ffff:169.254.169.254", port or 0, 0, 0))],
    )
    with pytest.raises(ValueError):
        splunk_mod._assert_safe_endpoint("https://evil.example.com:8088/services/collector/event")


def test_assert_safe_endpoint_rejects_unspecified(monkeypatch):
    monkeypatch.setattr(
        splunk_mod.socket, "getaddrinfo",
        lambda host, port, *a, **k: [(2, 1, 6, "", ("0.0.0.0", port or 0))],
    )
    with pytest.raises(ValueError):
        splunk_mod._assert_safe_endpoint("http://whatever:8088/x")


def test_hostname_resolving_to_metadata_is_blocked(monkeypatch):
    # the real attack: an innocent-looking NAME that resolves to metadata
    monkeypatch.setattr(
        splunk_mod.socket, "getaddrinfo",
        lambda host, port, *a, **k: [(2, 1, 6, "", ("169.254.169.254", port or 0))],
    )
    c = SplunkConnector(hec_url="https://innocent.example.com:8088", hec_token="t")
    with patch("core.integrations.splunk.requests.post") as post:
        assert c.send_event({"entity_id": "u1"}) is False
        post.assert_not_called()


def test_send_anomalies_validates_endpoint_once(monkeypatch):
    # perf regression guard: validation (DNS resolution) must be memoized, not
    # run once per anomaly — a 195k-anomaly run must not do 195k getaddrinfo.
    calls = {"n": 0}

    def counting_getaddrinfo(host, port, *a, **k):
        calls["n"] += 1
        return [(2, 1, 6, "", ("10.0.0.9", port or 0))]

    monkeypatch.setattr(splunk_mod.socket, "getaddrinfo", counting_getaddrinfo)
    c = SplunkConnector(hec_url="https://splunk.internal:8088", hec_token="t")
    with patch("core.integrations.splunk.requests.post") as post:
        post.return_value.status_code = 200
        sent = c.send_anomalies([{"entity_id": f"u{i}"} for i in range(50)], index="idx")
    assert sent == 50
    assert calls["n"] == 1  # resolved exactly once across 50 sends
