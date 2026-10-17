'''
Copyright 2019-Present The OpenUBA Platform Authors
splunk wiring tests (issue #99)

covers the settings integration (whitelist, masking, connectivity dispatch)
and the orchestrator's best-effort anomaly forwarding. Fully mocked.
'''

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from core.api_routers.settings import VALID_INTEGRATION_TYPES, _mask_sensitive_fields
from core.services import model_orchestrator as orch_mod
from core.services.model_orchestrator import ModelOrchestrator


# ─── settings wiring ─────────────────────────────────────────────────────────

def test_splunk_whitelisted():
    assert "splunk" in VALID_INTEGRATION_TYPES


def test_splunk_secrets_masked():
    masked = _mask_sensitive_fields({
        "token": "abcdef123456", "hec_token": "hectoken12345",
        "password": "pw12345678", "host": "https://s:8089",
    })
    assert masked["token"] != "abcdef123456"
    assert masked["hec_token"] != "hectoken12345"
    assert masked["password"] != "pw12345678"
    assert masked["host"] == "https://s:8089"


@pytest.mark.asyncio
async def test_test_splunk_delegates_to_connector():
    from core.api_routers.settings import _test_splunk
    with patch("core.integrations.splunk.SplunkConnector.test_connection",
               return_value={"status": "connected", "version": "9.0"}):
        result = await _test_splunk({"host": "https://s:8089", "token": "t"})
    assert result["status"] == "connected"


# ─── orchestrator forwarding ─────────────────────────────────────────────────

def _patch_db_with_splunk_row(config, enabled=True):
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (config, enabled)

    @contextmanager
    def ctx():
        yield db

    return ctx


def test_forward_skips_when_no_anomalies():
    orch = ModelOrchestrator()
    with patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        orch._forward_anomalies_to_splunk([])
    conn_cls.assert_not_called()


def test_forward_skips_when_disabled():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({"forward_anomalies": True}, enabled=False)
    with patch.object(orch_mod, "get_db_context", ctx), \
         patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        orch._forward_anomalies_to_splunk([{"a": 1}])
    conn_cls.assert_not_called()


def test_forward_skips_when_flag_off():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({"forward_anomalies": False, "hec_url": "x"})
    with patch.object(orch_mod, "get_db_context", ctx), \
         patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        orch._forward_anomalies_to_splunk([{"a": 1}])
    conn_cls.assert_not_called()


def test_forward_sends_when_enabled_and_flagged():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({
        "forward_anomalies": True, "hec_url": "https://s:8088",
        "hec_token": "t", "anomaly_index": "openuba",
    })
    anomalies = [{"entity_id": "u1"}, {"entity_id": "u2"}]
    with patch.object(orch_mod, "get_db_context", ctx), \
         patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        conn_cls.from_config.return_value.send_anomalies.return_value = 2
        orch._forward_anomalies_to_splunk(anomalies)
    conn_cls.from_config.return_value.send_anomalies.assert_called_once_with(
        anomalies, index="openuba"
    )


def test_forward_never_raises_on_error():
    orch = ModelOrchestrator()

    @contextmanager
    def boom():
        raise RuntimeError("db down")
        yield  # pragma: no cover

    with patch.object(orch_mod, "get_db_context", boom):
        # must not raise
        orch._forward_anomalies_to_splunk([{"a": 1}])


# ─── k8s-mode forwarding: re-read anomalies by run_id (#145) ─────────────────

def test_k8s_forward_reads_by_run_id_and_sends():
    orch = ModelOrchestrator()
    config_db = MagicMock()
    config_db.execute.return_value.fetchone.return_value = (
        {"forward_anomalies": True, "hec_url": "https://s:8088",
         "hec_token": "t", "anomaly_index": "openuba"}, True,
    )
    anomaly_db = MagicMock()
    anomaly_db.execute.return_value.fetchall.return_value = [
        ("u1", "user", 90.0, "behavioral", {}),
        ("u2", "user", 80.0, "behavioral", {}),
    ]
    dbs = [config_db, anomaly_db]

    @contextmanager
    def ctx():
        yield dbs.pop(0)

    with patch.object(orch_mod, "get_db_context", ctx), \
         patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        conn_cls.from_config.return_value.send_anomalies.return_value = 2
        orch._forward_run_anomalies_to_splunk_k8s("run-123")

    send = conn_cls.from_config.return_value.send_anomalies
    assert send.called
    args, kwargs = send.call_args
    assert kwargs.get("index") == "openuba"
    assert [a["entity_id"] for a in args[0]] == ["u1", "u2"]


def test_k8s_forward_skips_when_disabled():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({"forward_anomalies": False}, enabled=True)
    with patch.object(orch_mod, "get_db_context", ctx), \
         patch("core.integrations.splunk.SplunkConnector") as conn_cls:
        orch._forward_run_anomalies_to_splunk_k8s("run-123")
    conn_cls.from_config.assert_not_called()


def test_k8s_forward_never_raises_on_error():
    orch = ModelOrchestrator()

    @contextmanager
    def boom():
        raise RuntimeError("db down")
        yield  # pragma: no cover

    with patch.object(orch_mod, "get_db_context", boom):
        orch._forward_run_anomalies_to_splunk_k8s("run-123")  # must not raise


# ─── runner credential env bridging (#145 deferred fix) ──────────────────────

def test_splunk_runner_env_collects_creds():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({
        "host": "https://s:8089", "token": "tok", "hec_url": "https://s:8088",
        "hec_token": "hectok", "verify_ssl": False,
    }, enabled=True)
    with patch.object(orch_mod, "get_db_context", ctx):
        env = orch._splunk_runner_env()
    assert env["SPLUNK_HOST"] == "https://s:8089"
    assert env["SPLUNK_TOKEN"] == "tok"
    assert env["SPLUNK_HEC_URL"] == "https://s:8088"
    assert env["SPLUNK_HEC_TOKEN"] == "hectok"
    assert env["SPLUNK_VERIFY_SSL"] == "false"


def test_splunk_runner_env_empty_when_disabled():
    orch = ModelOrchestrator()
    ctx = _patch_db_with_splunk_row({"host": "x"}, enabled=False)
    with patch.object(orch_mod, "get_db_context", ctx):
        assert orch._splunk_runner_env() == {}


# ─── settings: masked secrets must not overwrite stored ones on save (#145) ──

def test_merge_preserving_secrets_keeps_unchanged_token():
    from core.api_routers.settings import _merge_preserving_secrets, _mask_sensitive_fields
    stored = {"host": "https://s:8089", "hec_token": "HECTOKEN-abcdef-1234567890",
              "token": "resttoken12345"}
    masked = _mask_sensitive_fields(stored)
    # UI echoes back the masked secrets unchanged + edits a non-secret field
    incoming = {"host": "https://s2:8089", "hec_token": masked["hec_token"], "token": masked["token"]}
    merged = _merge_preserving_secrets(incoming, stored)
    assert merged["hec_token"] == "HECTOKEN-abcdef-1234567890"   # real value kept
    assert merged["token"] == "resttoken12345"
    assert merged["host"] == "https://s2:8089"                   # non-secret edit applied


def test_merge_preserving_secrets_accepts_real_change():
    from core.api_routers.settings import _merge_preserving_secrets
    merged = _merge_preserving_secrets({"hec_token": "brandnewtoken67890"}, {"hec_token": "oldtoken12345"})
    assert merged["hec_token"] == "brandnewtoken67890"           # actual change persisted
