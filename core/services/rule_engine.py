"""
Rule evaluation engine for OpenUBA flow-based rules.

Evaluates flow graph DAGs against anomaly data after model inference,
producing alerts when rule conditions are met.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db.models import Alert, Rule

logger = logging.getLogger(__name__)


def _compare(value: float, operator: str, threshold: float) -> bool:
    """Compare a numeric value against a threshold using the given operator."""
    if operator == ">":
        return value > threshold
    elif operator == "<":
        return value < threshold
    elif operator == ">=":
        return value >= threshold
    elif operator == "<=":
        return value <= threshold
    elif operator == "==":
        return value == threshold
    elif operator == "!=":
        return value != threshold
    return False


def _parse_flow_graph(flow_graph: Any) -> Optional[Dict[str, Any]]:
    """Parse flow_graph from JSONB — handles both string and dict forms."""
    if flow_graph is None:
        return None
    if isinstance(flow_graph, str):
        try:
            return json.loads(flow_graph)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(flow_graph, dict):
        return flow_graph
    return None


def _rule_references_model(flow: Dict[str, Any], model_id: str) -> bool:
    """Check if a flow graph contains a model node referencing the given model_id."""
    for node in flow.get("nodes", []):
        if node.get("type") == "model":
            node_model_id = node.get("data", {}).get("modelId", "")
            if node_model_id == model_id:
                return True
    return False


def _build_incoming_edges(edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build a map of node_id -> list of source node_ids (incoming connections)."""
    incoming: Dict[str, List[str]] = {}
    for edge in edges:
        target = edge.get("target", "")
        source = edge.get("source", "")
        if target and source:
            incoming.setdefault(target, []).append(source)
    return incoming


class RuleEngine:
    """Evaluates flow-based rules against anomaly data to produce alerts."""

    MAX_ALERTS_PER_RUN = 500  # cap alerts per evaluation to prevent DB overload

    def evaluate_after_inference(
        self,
        model_id: str,
        anomalies_data: List[Dict[str, Any]],
        db: Session,
        max_alerts: Optional[int] = None,
    ) -> int:
        """
        Evaluate all enabled flow rules that reference the given model
        against the anomalies produced by inference.

        max_alerts overrides MAX_ALERTS_PER_RUN — used by the orchestrator
        to pass a remaining budget across batched calls.

        Returns the number of alerts fired.
        """
        alert_budget = max_alerts if max_alerts is not None else self.MAX_ALERTS_PER_RUN
        model_id_str = str(model_id)

        # get all enabled flow rules
        rules = (
            db.query(Rule)
            .filter(
                Rule.enabled == True,
                Rule.rule_type == "flow",
                Rule.flow_graph.isnot(None),
            )
            .all()
        )

        if not rules:
            return 0

        # filter to rules referencing this model
        relevant_rules: List[Rule] = []
        for rule in rules:
            flow = _parse_flow_graph(rule.flow_graph)
            if flow and _rule_references_model(flow, model_id_str):
                relevant_rules.append(rule)

        if not relevant_rules:
            logger.debug(f"no flow rules reference model {model_id_str}")
            return 0

        logger.info(
            f"evaluating {len(relevant_rules)} rule(s) against "
            f"{len(anomalies_data)} anomalie(s) from model {model_id_str}"
        )

        total_alerts = 0
        hit_cap = False

        for rule in relevant_rules:
            if hit_cap:
                break

            flow = _parse_flow_graph(rule.flow_graph)
            if not flow:
                continue

            nodes_map: Dict[str, Dict[str, Any]] = {
                n["id"]: n for n in flow.get("nodes", [])
            }
            incoming = _build_incoming_edges(flow.get("edges", []))
            alert_nodes = [
                n for n in flow.get("nodes", []) if n.get("type") == "alert"
            ]

            if not alert_nodes:
                continue

            for anomaly_data in anomalies_data:
                if total_alerts >= alert_budget:
                    logger.warning(
                        f"alert cap reached ({alert_budget}), "
                        f"stopping evaluation early"
                    )
                    hit_cap = True
                    break

                fired = self._evaluate_rule_for_anomaly(
                    rule=rule,
                    anomaly_data=anomaly_data,
                    model_id=model_id_str,
                    nodes_map=nodes_map,
                    incoming=incoming,
                    alert_nodes=alert_nodes,
                    db=db,
                )
                total_alerts += fired

                # commit in batches to avoid holding large transactions
                if total_alerts > 0 and total_alerts % 100 == 0:
                    db.commit()

        if total_alerts > 0:
            db.commit()
            logger.info(f"rule evaluation complete: {total_alerts} alert(s) fired")

        return total_alerts

    def _evaluate_rule_for_anomaly(
        self,
        rule: Rule,
        anomaly_data: Dict[str, Any],
        model_id: str,
        nodes_map: Dict[str, Dict[str, Any]],
        incoming: Dict[str, List[str]],
        alert_nodes: List[Dict[str, Any]],
        db: Session,
    ) -> int:
        """Evaluate a single rule against a single anomaly. Returns alerts fired count."""
        cache: Dict[str, Any] = {}
        fired = 0

        for alert_node in alert_nodes:
            alert_id = alert_node["id"]
            result = self._evaluate_node(
                node_id=alert_id,
                nodes_map=nodes_map,
                incoming=incoming,
                anomaly_data=anomaly_data,
                model_id=model_id,
                db=db,
                cache=cache,
            )

            if result:
                alert_data = alert_node.get("data", {})
                created = self._fire_alert(
                    rule=rule,
                    severity=alert_data.get("severity", "high"),
                    message=alert_data.get("message", "rule triggered"),
                    action=alert_data.get("action", "fire_alert"),
                    anomaly_data=anomaly_data,
                    db=db,
                )
                if created:
                    fired += 1

        return fired

    def _evaluate_node(
        self,
        node_id: str,
        nodes_map: Dict[str, Dict[str, Any]],
        incoming: Dict[str, List[str]],
        anomaly_data: Dict[str, Any],
        model_id: str,
        db: Session,
        cache: Dict[str, Any],
    ) -> Any:
        """Recursively evaluate a node in the flow graph. Returns the node's output value."""
        if node_id in cache:
            return cache[node_id]

        node = nodes_map.get(node_id)
        if not node:
            cache[node_id] = None
            return None

        node_type = node.get("type", "")
        data = node.get("data", {})

        # get input values from upstream nodes
        input_ids = incoming.get(node_id, [])
        input_values = [
            self._evaluate_node(
                iid, nodes_map, incoming, anomaly_data, model_id, db, cache
            )
            for iid in input_ids
        ]

        result: Any = None

        if node_type == "model":
            # model output node — return risk_score or has_anomaly from the anomaly
            output_type = data.get("output", "risk_score")
            if output_type == "risk_score":
                risk = anomaly_data.get("risk_score")
                result = float(risk) if risk is not None else 0.0
            elif output_type == "has_anomaly":
                result = True  # the anomaly exists, so has_anomaly is true

        elif node_type == "anomaly":
            # anomaly condition node — check if anomaly matches filters
            matches = True
            min_risk = data.get("minRiskScore")
            if min_risk is not None and min_risk != "":
                risk = anomaly_data.get("risk_score", 0)
                risk_val = float(risk) if risk is not None else 0.0
                if risk_val < float(min_risk):
                    matches = False

            entity_type_filter = data.get("entityType", "any")
            if entity_type_filter and entity_type_filter != "any":
                if anomaly_data.get("entity_type", "user") != entity_type_filter:
                    matches = False

            anomaly_type_filter = data.get("anomalyType", "")
            if anomaly_type_filter:
                if anomaly_data.get("anomaly_type", "") != anomaly_type_filter:
                    matches = False

            result = matches

        elif node_type == "case":
            # case condition node — check cases table
            case_event = data.get("caseEvent", "created")
            if case_event == "created":
                # check if any open case exists for this entity
                entity_id = anomaly_data.get("entity_id", "")
                if entity_id:
                    row = db.execute(
                        text(
                            "SELECT COUNT(*) FROM cases c "
                            "JOIN case_anomalies ca ON ca.case_id = c.id "
                            "JOIN anomalies a ON a.id = ca.anomaly_id "
                            "WHERE a.entity_id = :entity_id AND c.status != 'closed'"
                        ),
                        {"entity_id": entity_id},
                    ).scalar()
                    result = (row or 0) > 0
                else:
                    result = False
            elif case_event == "severity_match":
                target_sev = data.get("caseSeverity", "high")
                entity_id = anomaly_data.get("entity_id", "")
                if entity_id:
                    row = db.execute(
                        text(
                            "SELECT COUNT(*) FROM cases c "
                            "JOIN case_anomalies ca ON ca.case_id = c.id "
                            "JOIN anomalies a ON a.id = ca.anomaly_id "
                            "WHERE a.entity_id = :entity_id "
                            "AND c.severity = :severity AND c.status != 'closed'"
                        ),
                        {"entity_id": entity_id, "severity": target_sev},
                    ).scalar()
                    result = (row or 0) > 0
                else:
                    result = False
            else:
                result = False

        elif node_type == "comparison":
            # comparison node — compare input against threshold
            operator = data.get("operator", ">")
            threshold_str = data.get("value", "0")
            try:
                threshold = float(threshold_str)
            except (ValueError, TypeError):
                threshold = 0.0

            input_val = input_values[0] if input_values else 0.0
            if isinstance(input_val, bool):
                input_val = 1.0 if input_val else 0.0
            elif input_val is None:
                input_val = 0.0
            else:
                try:
                    input_val = float(input_val)
                except (ValueError, TypeError):
                    input_val = 0.0

            result = _compare(input_val, operator, threshold)

        elif node_type == "and":
            # AND gate — all inputs must be truthy
            result = all(bool(v) for v in input_values) if input_values else False

        elif node_type == "or":
            # OR gate — any input must be truthy
            result = any(bool(v) for v in input_values) if input_values else False

        elif node_type == "not":
            # NOT gate — invert single input
            result = not bool(input_values[0]) if input_values else True

        elif node_type == "alert":
            # alert node — truthy if any input is truthy
            result = any(bool(v) for v in input_values) if input_values else False

        else:
            result = None

        cache[node_id] = result
        return result

    def _fire_alert(
        self,
        rule: Rule,
        severity: str,
        message: str,
        action: str,
        anomaly_data: Dict[str, Any],
        db: Session,
    ) -> bool:
        """
        Create an alert record. Returns True if alert was created,
        False if deduplicated (same rule+entity+severity within 1 hour).
        """
        entity_id = str(anomaly_data.get("entity_id", "unknown"))
        entity_type = anomaly_data.get("entity_type", "user")

        # dedup: check if same alert fired recently
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        existing = db.execute(
            text(
                "SELECT COUNT(*) FROM alerts "
                "WHERE rule_id = :rule_id AND entity_id = :entity_id "
                "AND severity = :severity AND created_at > :cutoff"
            ),
            {
                "rule_id": str(rule.id),
                "entity_id": entity_id,
                "severity": severity,
                "cutoff": one_hour_ago,
            },
        ).scalar()

        if existing and existing > 0:
            logger.debug(
                f"dedup: skipping alert for rule={rule.name} entity={entity_id}"
            )
            return False

        # build context
        context = {
            "risk_score": anomaly_data.get("risk_score"),
            "anomaly_type": anomaly_data.get("anomaly_type"),
            "model_id": anomaly_data.get("model_id"),
            "action": action,
        }
        # include anomaly details if available
        if anomaly_data.get("details"):
            context["anomaly_details"] = anomaly_data["details"]

        alert = Alert(
            id=uuid.uuid4(),
            rule_id=rule.id,
            severity=severity,
            message=message,
            entity_id=entity_id,
            entity_type=entity_type,
            alert_context=context,
            acknowledged=False,
        )
        db.add(alert)

        # update rule last_triggered_at
        rule.last_triggered_at = datetime.utcnow()

        logger.info(
            f"alert fired: rule={rule.name} entity={entity_id} "
            f"severity={severity} action={action}"
        )
        return True
