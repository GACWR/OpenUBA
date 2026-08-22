# Datasets & Detection Evaluation

This guide covers how test data flows through OpenUBA and how to **evaluate** a
model's detections against known ground truth — the "Data Ingestion & Testing"
capability from issue #35.

## Datasets on disk

Raw logs live under `test_datasets/<dataset>/<log_type>/<file>`. OpenUBA ships
one real capture, `toy_1` (Zeek + Bluecoat: `proxy`, `dns`, `ssh`, `dhcp`).

On startup (local mode) the ingestion service walks every dataset directory and
fans each log type out into two queryable surfaces:

- a **Spark table** `"<dataset>_<log_type>"` (e.g. `toy_1_proxy`)
- an **Elasticsearch index** `"openuba-<log_type>-<dataset>"` (e.g. `openuba-proxy-toy_1`)

### Adding another dataset

Drop a second capture in the same layout — for example
`test_datasets/labeled_1/{proxy,ssh,dns}/…` — and it is ingested automatically;
no code change is needed. (Previously a whitelist hard-limited ingestion to
`toy_1`.) Keep per-log-type formats consistent with the parser:

| log types | separator | header | encoding |
|---|---|---|---|
| `proxy` / `bluecoat` | space | yes | ISO-8859-1 |
| `ssh` / `dns` / `dhcp` | tab | no | UTF-8 |

Ingest on demand via the API:

```bash
curl -X POST "$API/api/v1/data/ingest" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"dataset_name": "labeled_1", "ingest_to_spark": true, "ingest_to_es": true}'
```

The new tables/indices then appear automatically in the model-run dataset
picker and on the Data page.

## Ground truth

To *test* detections you need to know which entities are actually malicious. For
a labeled/benchmark dataset, record its known-bad `entity_id`s (the identity
column the model carries onto each anomaly — e.g. `cs-username` for proxy, the
uid/host for ssh/dns). Keep that answer key with the dataset, e.g.
`test_datasets/labeled_1/ground_truth.json`:

```json
{
  "dataset": "labeled_1",
  "malicious_entities": ["u_exfil_01", "u_brute_01", "h_beacon_01"],
  "scenarios": {
    "data_exfil": ["u_exfil_01"],
    "brute_force": ["u_brute_01"],
    "dns_beacon": ["h_beacon_01"]
  }
}
```

Ground truth here is the offline benchmark answer key. It complements — it does
not replace — the live analyst-labeling surface (`UserFeedback`, with
`feedback_type` = `true_positive` / `false_positive`), which captures dispositions
on real anomalies in production.

## Evaluating a run

Run a model against a dataset the usual way (via the UI, SDK, or API — see the
model-run docs), note the resulting `run_id`, then score its detections:

```python
import openuba
openuba.configure(api_url="http://localhost:8000", token="<token>")

metrics = openuba.evaluate_run(
    run_id,
    malicious_entities=["u_exfil_01", "u_brute_01", "h_beacon_01"],
    all_entities=[...],          # optional: full population, for FP-rate / TNs
    threshold=50,                # risk_score at/above which an entity is "flagged"
    scenarios={...},             # optional: per-scenario recall
)
print(metrics["precision"], metrics["recall"], metrics["f1"])
```

Under the hood this reads the run's anomalies and scores them:

- **Read** — anomalies are fetched scoped to the run:
  `GET /api/v1/anomalies?run_id=<id>` (also `openuba.query_anomalies(run_id=…)`,
  or GraphQL `allAnomalies(condition:{runId})`).
- **Score** — `POST /api/v1/evaluate/run` computes entity-level
  precision / recall / F1 / false-positive-rate (+ per-scenario recall) with the
  shared `core.services.detection_eval` scorer.

An entity counts as *flagged* if it has an anomaly whose `risk_score` meets the
threshold, mirroring how OpenUBA models emit one anomaly per event with a 0–100
score.

## Tracking results across runs

The returned metrics are JSONB-friendly and are meant to be stored on an
**experiment run** so you can compare detectors and tunings over time:

```python
exp = openuba.create_experiment("labeled_1 benchmark")
openuba.add_experiment_run(exp["id"], model_id=model_id, metrics=metrics)
openuba.compare_experiment_runs(exp["id"])
```

This reuses OpenUBA's existing experiments/metrics machinery rather than a
separate store.
