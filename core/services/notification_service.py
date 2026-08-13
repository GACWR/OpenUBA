'''
Copyright 2019-Present The OpenUBA Platform Authors
notification service — realtime alert delivery over SMTP (email) and in-app.

Config is read from the integration_settings table (integration_type="smtp"),
mirroring how ChatService loads LLM provider config, and falls back to
environment variables. Nothing here raises to the caller: delivery is
best-effort so a mail outage can never block alert creation.
'''

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_db_context
from core.db.models import Notification

logger = logging.getLogger(__name__)

# actions (from the rule-canvas alert node) that should send notifications
NOTIFY_ACTIONS = {"notify", "fire_alert_and_notify", "notify_and_open_case"}


def _as_recipient_list(value: Any) -> List[str]:
    '''normalize a recipients value (list or comma/space string) to a clean list'''
    if not value:
        return []
    if isinstance(value, str):
        parts = value.replace(";", ",").replace(" ", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        return []
    return [str(p).strip() for p in parts if str(p).strip()]


class EmailService:
    '''
    minimal SMTP sender. loads config from integration_settings (type="smtp"),
    falls back to SMTP_* env vars. send() never raises — returns True/False.
    '''

    def _load_smtp_config(self) -> Optional[Dict[str, Any]]:
        '''return smtp config dict if enabled+configured, else None'''
        config: Dict[str, Any] = {}
        try:
            with get_db_context() as db:
                row = db.execute(text(
                    "SELECT config, enabled FROM integration_settings "
                    "WHERE integration_type = 'smtp'"
                )).fetchone()
            if row and row[1]:  # enabled
                config = dict(row[0]) if row[0] else {}
        except Exception as e:
            logger.warning(f"failed to load smtp config from db: {e}")

        # env fallback for any field not set in the db row
        host = config.get("host") or os.environ.get("SMTP_HOST", "")
        if not host:
            return None

        def _flag(cfg_key: str, env_key: str, default: bool) -> bool:
            if cfg_key in config:
                return bool(config[cfg_key])
            env = os.environ.get(env_key)
            if env is None:
                return default
            return env.strip().lower() in ("1", "true", "yes", "on")

        return {
            "host": host,
            "port": int(config.get("port") or os.environ.get("SMTP_PORT", 587)),
            "username": config.get("username") or os.environ.get("SMTP_USERNAME", ""),
            "password": config.get("password") or os.environ.get("SMTP_PASSWORD", ""),
            "from_addr": (
                config.get("from_addr")
                or config.get("from")
                or os.environ.get("SMTP_FROM")
                or config.get("username")
                or os.environ.get("SMTP_USERNAME", "openuba@localhost")
            ),
            "use_tls": _flag("use_tls", "SMTP_USE_TLS", True),
            "use_ssl": _flag("use_ssl", "SMTP_USE_SSL", False),
            "default_recipients": _as_recipient_list(
                config.get("default_recipients")
                or os.environ.get("SMTP_DEFAULT_RECIPIENTS", "")
            ),
        }

    def is_configured(self) -> bool:
        return self._load_smtp_config() is not None

    def default_recipients(self) -> List[str]:
        cfg = self._load_smtp_config()
        return cfg["default_recipients"] if cfg else []

    def send(
        self,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        timeout: int = 10,
    ) -> bool:
        '''send an email. returns True on success, False otherwise (never raises).'''
        recipients = _as_recipient_list(to)
        if not recipients:
            logger.debug("email send skipped: no recipients")
            return False

        cfg = self._load_smtp_config()
        if not cfg:
            logger.debug("email send skipped: smtp not configured/enabled")
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = cfg["from_addr"]
        msg["To"] = ", ".join(recipients)
        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        try:
            if cfg["use_ssl"]:
                context = ssl.create_default_context()
                server: smtplib.SMTP = smtplib.SMTP_SSL(
                    cfg["host"], cfg["port"], timeout=timeout, context=context
                )
            else:
                server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout)
                if cfg["use_tls"]:
                    server.starttls(context=ssl.create_default_context())
            with server:
                if cfg["username"] and cfg["password"]:
                    server.login(cfg["username"], cfg["password"])
                server.send_message(msg)
            logger.info(f"alert email sent to {len(recipients)} recipient(s)")
            return True
        except Exception as e:
            logger.error(f"failed to send alert email: {e}")
            return False


class AlertNotifier:
    '''
    orchestrates realtime delivery for a fired alert: SMTP email (to the rule's
    recipients or the configured default list) plus an in-app Notification for
    every active user. Best-effort — failures are logged, never raised.
    '''

    def __init__(self, email_service: Optional[EmailService] = None):
        self.email = email_service or EmailService()

    @staticmethod
    def should_notify(action: Optional[str]) -> bool:
        return bool(action) and action in NOTIFY_ACTIONS

    def notify(
        self,
        db: Session,
        *,
        rule_name: str,
        severity: str,
        message: str,
        entity_id: str,
        entity_type: str,
        alert_id: Optional[str] = None,
        recipients: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''deliver email + in-app notifications for one alert. returns a summary.'''
        subject = f"[OpenUBA] {severity.upper()} alert: {rule_name}"
        lines = [
            f"Rule: {rule_name}",
            f"Severity: {severity}",
            f"Entity: {entity_type}/{entity_id}",
            f"Message: {message}",
        ]
        if context:
            if context.get("risk_score") is not None:
                lines.append(f"Risk score: {context.get('risk_score')}")
            if context.get("anomaly_type"):
                lines.append(f"Anomaly type: {context.get('anomaly_type')}")
        body_text = "\n".join(lines)

        summary = {"email_sent": False, "in_app_created": 0}

        # 1) email delivery (rule recipients override the configured default list)
        to = _as_recipient_list(recipients) or self.email.default_recipients()
        if to:
            summary["email_sent"] = self.email.send(to, subject, body_text)

        # 2) in-app notifications for every active user (reuses the notifications
        #    center already wired into the frontend + notifications router)
        try:
            user_rows = db.execute(text(
                "SELECT id FROM users WHERE is_active = true"
            )).fetchall()
            for (user_id,) in user_rows:
                db.add(Notification(
                    user_id=user_id,
                    title=subject,
                    message=message,
                    type="alert",
                    link="/alerts",
                ))
            summary["in_app_created"] = len(user_rows)
        except Exception as e:
            logger.error(f"failed to create in-app notifications: {e}")

        return summary
