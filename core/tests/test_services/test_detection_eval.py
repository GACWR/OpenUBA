'''
Copyright 2019-Present The OpenUBA Platform Authors
detection evaluation tests (issue #35)

pure unit tests for the entity-level scoring used to evaluate a model run
against a labeled dataset. No DB/Docker — runs in the CI unit job.
'''

from types import SimpleNamespace

import pytest

from core.services.detection_eval import (
    EvaluationResult,
    evaluate_detections,
    flagged_entities,
)


def _anom(entity_id, risk_score, anomaly_type="statistical_outlier"):
    return {"entity_id": entity_id, "risk_score": risk_score, "anomaly_type": anomaly_type}


# ─── flagged_entities ────────────────────────────────────────────────────────

def test_flagged_entities_respects_threshold():
    anoms = [_anom("u1", 90), _anom("u2", 20), _anom("u3", 50)]
    assert flagged_entities(anoms, threshold=50) == {"u1", "u3"}
    assert flagged_entities(anoms, threshold=95) == set()


def test_flagged_entities_dedups_multiple_events_per_entity():
    anoms = [_anom("u1", 60), _anom("u1", 80), _anom("u1", 10)]
    assert flagged_entities(anoms, threshold=50) == {"u1"}


def test_flagged_entities_handles_orm_rows_and_bad_values():
    rows = [SimpleNamespace(entity_id="u1", risk_score="88"),
            SimpleNamespace(entity_id="u2", risk_score=None),
            SimpleNamespace(entity_id=None, risk_score=99)]
    assert flagged_entities(rows, threshold=50) == {"u1"}


# ─── evaluate_detections ─────────────────────────────────────────────────────

def test_perfect_detection():
    anoms = [_anom("bad1", 95), _anom("bad2", 80)]
    r = evaluate_detections(anoms, malicious_entities=["bad1", "bad2"],
                            all_entities=["bad1", "bad2", "good1", "good2"], threshold=50)
    assert isinstance(r, EvaluationResult)
    assert r.precision == 1.0 and r.recall == 1.0 and r.f1 == 1.0
    assert r.false_positive_rate == 0.0
    assert r.true_positives == 2 and r.false_negatives == 0
    assert r.false_positives == 0 and r.true_negatives == 2
    assert r.missed_entities == []


def test_missed_malicious_lowers_recall():
    anoms = [_anom("bad1", 95)]  # bad2 not flagged
    r = evaluate_detections(anoms, malicious_entities=["bad1", "bad2"],
                            all_entities=["bad1", "bad2", "good1"], threshold=50)
    assert r.recall == 0.5
    assert r.false_negatives == 1
    assert r.missed_entities == ["bad2"]


def test_false_positive_lowers_precision():
    anoms = [_anom("bad1", 95), _anom("good1", 88)]
    r = evaluate_detections(anoms, malicious_entities=["bad1"],
                            all_entities=["bad1", "good1", "good2"], threshold=50)
    assert r.recall == 1.0
    assert r.precision == 0.5
    assert r.false_positives == 1
    # fpr = fp / (fp+tn) = 1 / (1 + 1) = 0.5  (good2 is a true negative)
    assert r.false_positive_rate == 0.5


def test_threshold_gates_low_risk_events():
    anoms = [_anom("bad1", 40)]  # below threshold → not flagged
    r = evaluate_detections(anoms, malicious_entities=["bad1"],
                            all_entities=["bad1", "good1"], threshold=50)
    assert r.recall == 0.0 and r.true_positives == 0 and r.false_negatives == 1


def test_per_scenario_recall():
    anoms = [_anom("exfil1", 95), _anom("brute1", 90)]  # beacon1 missed
    r = evaluate_detections(
        anoms,
        malicious_entities=["exfil1", "brute1", "beacon1"],
        all_entities=["exfil1", "brute1", "beacon1", "good1"],
        threshold=50,
        scenarios={"data_exfil": ["exfil1"], "brute_force": ["brute1"], "dns_beacon": ["beacon1"]},
    )
    assert r.per_scenario_recall["data_exfil"] == 1.0
    assert r.per_scenario_recall["brute_force"] == 1.0
    assert r.per_scenario_recall["dns_beacon"] == 0.0


def test_empty_inputs_do_not_divide_by_zero():
    r = evaluate_detections([], malicious_entities=[], all_entities=[])
    assert r.precision == 0.0 and r.recall == 0.0 and r.f1 == 0.0
    assert r.false_positive_rate == 0.0


def test_to_dict_is_jsonb_friendly():
    anoms = [_anom("bad1", 95)]
    r = evaluate_detections(anoms, malicious_entities=["bad1"], all_entities=["bad1", "good1"])
    d = r.to_dict()
    # keys the experiments UI/compare would chart
    for k in ("precision", "recall", "f1", "false_positive_rate", "threshold"):
        assert k in d and isinstance(d[k], float)
    assert isinstance(d["flagged_entities"], list)
