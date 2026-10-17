'''
Copyright 2019-Present The OpenUBA Platform Authors
settings router SMTP tests (issue #25)

covers the smtp integration wiring: whitelist registration, password masking
on read, and the connectivity test (smtplib mocked). No container needed.
'''

from unittest.mock import patch

import pytest

from core.api_routers.settings import (
    VALID_INTEGRATION_TYPES,
    _mask_sensitive_fields,
    _test_smtp,
)


def test_smtp_is_whitelisted():
    assert "smtp" in VALID_INTEGRATION_TYPES


def test_password_is_masked():
    masked = _mask_sensitive_fields({"password": "supersecretvalue", "host": "smtp.x"})
    assert masked["password"] != "supersecretvalue"
    assert masked["host"] == "smtp.x"  # non-sensitive fields untouched


def test_api_key_still_masked():
    masked = _mask_sensitive_fields({"api_key": "sk-abcdefghijklmnop"})
    assert masked["api_key"] != "sk-abcdefghijklmnop"


@pytest.mark.asyncio
async def test_test_smtp_reports_error_without_host():
    result = await _test_smtp({})
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_test_smtp_connected_with_starttls():
    cfg = {"host": "smtp.example.com", "port": 587, "use_tls": True,
           "username": "u", "password": "p"}
    with patch("smtplib.SMTP") as smtp_cls:
        result = await _test_smtp(cfg)
    assert result["status"] == "connected"
    smtp_cls.return_value.login.assert_called_once_with("u", "p")
