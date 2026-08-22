'''
Copyright 2019-Present The OpenUBA Platform Authors
tests for the evaluation api router (issue #35)

end-to-end through the API: seed a run + anomalies, POST /evaluate/run, and
check the detection metrics come back correct.
'''

from fastapi.testclient import TestClient


def _seed_run_with_anomalies(db_session):
    from core.repositories.model_repository import ModelRepository
    from core.repositories.anomaly_repository import AnomalyRepository
    from core.db.models import ModelVersion, ModelRun

    model = ModelRepository(db_session).create(
        name="eval_api_model", version="1.0.0", source_type="local_fs")
    ver = ModelVersion(model_id=model.id, version="1.0.0", status="registered")
    db_session.add(ver)
    db_session.flush()
    run = ModelRun(model_version_id=ver.id, run_type="infer", status="succeeded")
    db_session.add(run)
    db_session.flush()

    ar = AnomalyRepository(db_session)
    ar.create(model_id=model.id, entity_id="bad1", risk_score=95, run_id=run.id)
    ar.create(model_id=model.id, entity_id="good1", risk_score=10, run_id=run.id)
    return run


def test_evaluate_run_scores_detections(test_client: TestClient, db_session):
    run = _seed_run_with_anomalies(db_session)

    resp = test_client.post("/api/v1/evaluate/run", json={
        "run_id": str(run.id),
        "malicious_entities": ["bad1", "bad2"],
        "all_entities": ["bad1", "bad2", "good1"],
        "threshold": 50,
    })
    assert resp.status_code == 200, resp.text
    m = resp.json()
    # bad1 flagged (TP), bad2 never flagged (FN), good1 below threshold (TN)
    assert m["true_positives"] == 1
    assert m["false_negatives"] == 1
    assert m["recall"] == 0.5
    assert m["precision"] == 1.0
    assert m["missed_entities"] == ["bad2"]
    for k in ("f1", "false_positive_rate", "threshold"):
        assert k in m


def test_evaluate_run_empty_run_is_safe(test_client: TestClient, db_session):
    run = _seed_run_with_anomalies(db_session)
    # a run_id with no matching anomalies → zero metrics, no error
    from uuid import uuid4
    resp = test_client.post("/api/v1/evaluate/run", json={
        "run_id": str(uuid4()),
        "malicious_entities": ["bad1"],
        "all_entities": ["bad1", "good1"],
    })
    assert resp.status_code == 200, resp.text
    m = resp.json()
    assert m["recall"] == 0.0 and m["true_positives"] == 0
