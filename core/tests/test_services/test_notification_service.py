'''
Copyright 2019-Present The OpenUBA Platform Authors
notification service tests (realtime alerts — issue #25)

fast unit tests: SMTP config loading, recipient normalization, email send
(smtplib mocked), notify-action gating, and end-to-end dispatch with a
mocked db + email service. No live SMTP server or database container needed.
'''

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from core.services import notification_service as ns
from core.services.notification_service import (
    AlertNotifier,
    EmailService,
    NOTIFY_ACTIONS,
    _as_recipient_list,
)


# ─── recipient normalization ─────────────────────────────────────────────────

def test_as_recipient_list_handles_all_shapes():
    assert _as_recipient_list(None) == []
    assert _as_recipient_list("") == []
    assert _as_recipient_list("a@x.com") == ["a@x.com"]
    assert _as_recipient_list("a@x.com, b@x.com") == ["a@x.com", "b@x.com"]
    assert _as_recipient_list("a@x.com; b@x.com c@x.com") == ["a@x.com", "b@x.com", "c@x.com"]
    assert _as_recipient_list([" a@x.com ", "b@x.com"]) == ["a@x.com", "b@x.com"]
    assert _as_recipient_list(123) == []


# ─── config loading ──────────────────────────────────────────────────────────

@contextmanager
def _raise_ctx():
    raise RuntimeError("no db in unit test")
    yield  # pragma: no cover


def test_load_smtp_config_env_fallback(monkeypatch):
    '''when the db is unavailable, config comes from SMTP_* env vars'''
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USERNAME", "bot@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_DEFAULT_RECIPIENTS", "soc@example.com, oncall@example.com")
    monkeypatch.setenv("SMTP_USE_TLS", "true")

    with patch.object(ns, "get_db_context", _raise_ctx):
        cfg = EmailService()._load_smtp_config()

    assert cfg is not None
    assert cfg["host"] == "smtp.example.com"
    assert cfg["port"] == 2525
    assert cfg["username"] == "bot@example.com"
    assert cfg["use_tls"] is True
    assert cfg["default_recipients"] == ["soc@example.com", "oncall@example.com"]


def test_load_smtp_config_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with patch.object(ns, "get_db_context", _raise_ctx):
        assert EmailService()._load_smtp_config() is None
        assert EmailService().is_configured() is False


def test_db_config_takes_precedence(monkeypatch):
    '''an enabled integration_settings row is used over env'''
    monkeypatch.delenv("SMTP_HOST", raising=False)

    fake_db = MagicMock()
    fake_db.execute.return_value.fetchone.return_value = (
        {"host": "mail.internal", "port": 465, "use_ssl": True,
         "default_recipients": ["team@internal"]},
        True,  # enabled
    )

    @contextmanager
    def fake_ctx():
        yield fake_db

    with patch.object(ns, "get_db_context", fake_ctx):
        cfg = EmailService()._load_smtp_config()

    assert cfg["host"] == "mail.internal"
    assert cfg["port"] == 465
    assert cfg["use_ssl"] is True


# ─── email sending (smtplib mocked) ──────────────────────────────────────────

def test_send_returns_false_without_recipients():
    svc = EmailService()
    with patch.object(EmailService, "_load_smtp_config", return_value={"host": "x"}):
        assert svc.send([], "subj", "body") is False


def test_send_returns_false_when_not_configured():
    svc = EmailService()
    with patch.object(EmailService, "_load_smtp_config", return_value=None):
        assert svc.send(["a@x.com"], "subj", "body") is False


def test_send_uses_starttls_and_login():
    cfg = {
        "host": "smtp.example.com", "port": 587, "username": "u", "password": "p",
        "from_addr": "from@x.com", "use_tls": True, "use_ssl": False,
        "default_recipients": [],
    }
    with patch.object(EmailService, "_load_smtp_config", return_value=cfg), \
         patch.object(ns.smtplib, "SMTP") as smtp_cls:
        server = smtp_cls.return_value
        ok = EmailService().send(["a@x.com"], "subj", "body text")

    assert ok is True
    smtp_cls.assert_called_once()
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("u", "p")
    server.send_message.assert_called_once()


def test_send_uses_ssl_transport():
    cfg = {
        "host": "smtp.example.com", "port": 465, "username": "", "password": "",
        "from_addr": "from@x.com", "use_tls": False, "use_ssl": True,
        "default_recipients": [],
    }
    with patch.object(EmailService, "_load_smtp_config", return_value=cfg), \
         patch.object(ns.smtplib, "SMTP_SSL") as smtp_ssl:
        ok = EmailService().send(["a@x.com"], "subj", "body")

    assert ok is True
    smtp_ssl.assert_called_once()
    # no credentials → no login attempt
    smtp_ssl.return_value.login.assert_not_called()


def test_send_swallows_errors():
    cfg = {
        "host": "smtp.example.com", "port": 587, "username": "", "password": "",
        "from_addr": "from@x.com", "use_tls": True, "use_ssl": False,
        "default_recipients": [],
    }
    with patch.object(EmailService, "_load_smtp_config", return_value=cfg), \
         patch.object(ns.smtplib, "SMTP", side_effect=OSError("connection refused")):
        assert EmailService().send(["a@x.com"], "subj", "body") is False


# ─── notify-action gating ────────────────────────────────────────────────────

@pytest.mark.parametrize("action,expected", [
    ("notify", True),
    ("fire_alert_and_notify", True),
    ("notify_and_open_case", True),
    ("fire_alert", False),
    ("open_case", False),
    ("", False),
    (None, False),
])
def test_should_notify(action, expected):
    assert AlertNotifier.should_notify(action) is expected


def test_notify_actions_membership():
    assert "notify" in NOTIFY_ACTIONS
    assert "fire_alert" not in NOTIFY_ACTIONS


# ─── end-to-end dispatch (email + in-app), mocked ────────────────────────────

def _fake_db_with_users(n=3):
    db = MagicMock()
    db.execute.return_value.fetchall.return_value = [(f"user-{i}",) for i in range(n)]
    return db


def test_notify_sends_email_to_rule_recipients_and_creates_in_app():
    email = MagicMock(spec=EmailService)
    email.send.return_value = True
    email.default_recipients.return_value = ["default@x.com"]
    db = _fake_db_with_users(3)

    summary = AlertNotifier(email_service=email).notify(
        db,
        rule_name="Impossible travel",
        severity="high",
        message="user logged in from two continents",
        entity_id="u123",
        entity_type="user",
        recipients="analyst@x.com",
        context={"risk_score": 0.97, "anomaly_type": "geo"},
    )

    # rule recipients override the default list (normalized to a list)
    args, _ = email.send.call_args
    assert args[0] == ["analyst@x.com"]
    assert "Impossible travel" in args[1]  # subject includes rule name
    assert summary["email_sent"] is True
    # one in-app notification per active user
    assert summary["in_app_created"] == 3
    assert db.add.call_count == 3


def test_notify_falls_back_to_default_recipients():
    email = MagicMock(spec=EmailService)
    email.send.return_value = True
    email.default_recipients.return_value = ["soc@x.com"]
    db = _fake_db_with_users(1)

    AlertNotifier(email_service=email).notify(
        db, rule_name="r", severity="low", message="m",
        entity_id="e", entity_type="user", recipients=None,
    )

    args, _ = email.send.call_args
    assert args[0] == ["soc@x.com"]


def test_notify_still_creates_in_app_when_no_email_recipients():
    email = MagicMock(spec=EmailService)
    email.default_recipients.return_value = []
    db = _fake_db_with_users(2)

    summary = AlertNotifier(email_service=email).notify(
        db, rule_name="r", severity="medium", message="m",
        entity_id="e", entity_type="user",
    )

    email.send.assert_not_called()
    assert summary["email_sent"] is False
    assert summary["in_app_created"] == 2
