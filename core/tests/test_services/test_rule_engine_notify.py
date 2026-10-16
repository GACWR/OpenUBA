'''
Copyright 2019-Present The OpenUBA Platform Authors
rule engine → notification wiring tests (issue #25)

verifies that a fired alert dispatches realtime notifications only when the
alert node's action is a notify action, and threads the node's recipients
through. Uses a mocked db + patched AlertNotifier (no container needed).
'''

from unittest.mock import MagicMock, patch

import pytest

from core.services import rule_engine as re_mod
from core.services.rule_engine import RuleEngine


def _fake_db_no_dedup():
    '''db whose dedup COUNT(*) returns 0 so the alert is always created'''
    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    return db


def _rule():
    rule = MagicMock()
    rule.name = "Impossible travel"
    rule.id = "11111111-1111-1111-1111-111111111111"
    return rule


ANOMALY = {"entity_id": "u1", "entity_type": "user", "risk_score": 0.9}


def test_fire_alert_dispatches_on_notify_action():
    db = _fake_db_no_dedup()
    with patch.object(re_mod, "AlertNotifier") as notifier_cls:
        notifier_cls.should_notify.return_value = True
        created = RuleEngine()._fire_alert(
            rule=_rule(), severity="high", message="msg",
            action="notify", anomaly_data=ANOMALY, db=db,
            recipients="soc@x.com",
        )

    assert created is True
    notifier_cls.return_value.notify.assert_called_once()
    # recipients from the node are threaded through
    _, kwargs = notifier_cls.return_value.notify.call_args
    assert kwargs["recipients"] == "soc@x.com"


def test_fire_alert_skips_dispatch_on_plain_action():
    db = _fake_db_no_dedup()
    with patch.object(re_mod, "AlertNotifier") as notifier_cls:
        notifier_cls.should_notify.return_value = False
        created = RuleEngine()._fire_alert(
            rule=_rule(), severity="high", message="msg",
            action="fire_alert", anomaly_data=ANOMALY, db=db,
        )

    assert created is True
    notifier_cls.return_value.notify.assert_not_called()


def test_fire_alert_notification_failure_does_not_break_alerting():
    db = _fake_db_no_dedup()
    with patch.object(re_mod, "AlertNotifier") as notifier_cls:
        notifier_cls.should_notify.return_value = True
        notifier_cls.return_value.notify.side_effect = RuntimeError("smtp down")
        # must not raise — alert creation is the priority
        created = RuleEngine()._fire_alert(
            rule=_rule(), severity="high", message="msg",
            action="notify", anomaly_data=ANOMALY, db=db,
        )

    assert created is True
    db.add.assert_called_once()  # the alert was still added
