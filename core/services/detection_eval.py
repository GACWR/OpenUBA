'''
Copyright 2019-Present The OpenUBA Platform Authors
detection evaluation — score a model run's anomalies against known ground truth.

This is the one genuinely-new capability behind issue #35 ("Data Ingestion &
Testing"): given the anomalies a run produced and the set of entities that are
known to be malicious in a labeled dataset, compute standard detection metrics
(precision / recall / F1 / false-positive rate) at the ENTITY level.

Deliberately dependency-light (pure Python stdlib, 3.9-compatible) so it runs in
the unit test job with no infra. The results are meant to be stored in the
existing ExperimentRun.metrics (JSONB) via the experiments API/SDK, and the
ground-truth labels can be persisted through the existing UserFeedback surface —
this module only computes the math.
'''

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional, Set


@dataclass
class EvaluationResult:
    '''entity-level detection metrics for one run against a labeled dataset'''
    threshold: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    flagged_entities: List[str] = field(default_factory=list)
    missed_entities: List[str] = field(default_factory=list)
    # recall per scenario/anomaly-type when the ground truth carries scenarios
    per_scenario_recall: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        '''shape suitable for ExperimentRun.metrics (JSONB)'''
        return asdict(self)


def _entity_of(anomaly: Any) -> Optional[str]:
    '''pull the entity id from an anomaly dict or ORM row'''
    if isinstance(anomaly, dict):
        val = anomaly.get("entity_id")
    else:
        val = getattr(anomaly, "entity_id", None)
    return None if val is None else str(val)


def _risk_of(anomaly: Any) -> float:
    if isinstance(anomaly, dict):
        val = anomaly.get("risk_score")
    else:
        val = getattr(anomaly, "risk_score", None)
    try:
        return float(val) if val is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def flagged_entities(anomalies: Iterable[Any], threshold: float = 50.0) -> Set[str]:
    '''
    entities the run flagged: any entity with an anomaly whose risk_score meets
    the threshold. Mirrors how OpenUBA models emit one anomaly per event with a
    0-100 risk_score, so an entity is "flagged" if any of its events scored high.
    '''
    out: Set[str] = set()
    for a in anomalies:
        ent = _entity_of(a)
        if ent is None:
            continue
        if _risk_of(a) >= threshold:
            out.add(ent)
    return out


def evaluate_detections(
    anomalies: Iterable[Any],
    malicious_entities: Iterable[str],
    all_entities: Optional[Iterable[str]] = None,
    threshold: float = 50.0,
    scenarios: Optional[Dict[str, Iterable[str]]] = None,
) -> EvaluationResult:
    '''
    Score a run's anomalies against ground truth.

    anomalies          — the run's anomalies (dicts or ORM rows with
                         entity_id + risk_score); typically read by run_id.
    malicious_entities — ground-truth set of entity_ids that are truly bad.
    all_entities       — the full population the run covered (to count true
                         negatives / false-positive rate). If omitted, it is the
                         union of malicious + flagged (TNR then unknown → 0 TNs).
    threshold          — risk_score at/above which an entity counts as flagged.
    scenarios          — optional {scenario_name: [entity_ids]} for per-scenario recall.
    '''
    malicious: Set[str] = {str(e) for e in malicious_entities}
    flagged: Set[str] = flagged_entities(anomalies, threshold)

    population: Set[str]
    if all_entities is not None:
        population = {str(e) for e in all_entities} | malicious | flagged
    else:
        population = malicious | flagged
    benign = population - malicious

    tp = len(flagged & malicious)
    fp = len(flagged & benign)
    fn = len(malicious - flagged)
    tn = len(benign - flagged)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    per_scenario: Dict[str, float] = {}
    if scenarios:
        for name, ents in scenarios.items():
            ents_set = {str(e) for e in ents}
            if not ents_set:
                continue
            caught = len(ents_set & flagged)
            per_scenario[name] = caught / len(ents_set)

    return EvaluationResult(
        threshold=float(threshold),
        precision=round(precision, 6),
        recall=round(recall, 6),
        f1=round(f1, 6),
        false_positive_rate=round(fpr, 6),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        flagged_entities=sorted(flagged),
        missed_entities=sorted(malicious - flagged),
        per_scenario_recall=per_scenario,
    )
