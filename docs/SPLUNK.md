# Splunk Integration

OpenUBA integrates with Splunk in both directions:

- **Input** — run a Splunk search and feed the results to a model as a data source.
- **Output** — forward detected anomalies back to Splunk via the HTTP Event Collector (HEC).

## Configuration

Configure Splunk under **Settings → Integrations → Splunk**, or via the API
(`PUT /api/v1/settings/integrations/splunk`). Config is stored in the
`integration_settings` table (no secrets in manifests) and the token / HEC
token / password are masked on read.

| Field | Purpose |
|---|---|
| `host` | REST management endpoint, e.g. `https://splunk:8089` (used for search) |
| `token` | REST bearer token (preferred), **or** |
| `username` / `password` | basic auth for the REST API |
| `hec_url` | HTTP Event Collector base, e.g. `https://splunk:8088` (used for output) |
| `hec_token` | HEC token |
| `anomaly_index` | Splunk index anomalies are forwarded to |
| `forward_anomalies` | when on, each inference run forwards its anomalies to Splunk |
| `verify_ssl` | verify TLS certificates (default on) |

Use **Test** in the settings panel to verify connectivity.

The model-runner container reads the same values from the environment when it
executes a search: `SPLUNK_HOST`, `SPLUNK_TOKEN`, `SPLUNK_USERNAME`,
`SPLUNK_PASSWORD`, `SPLUNK_VERIFY_SSL`.

## Using Splunk as a data source

Select `splunk` as the data source when training or running a model and pass a
search. Via the API:

```bash
curl -X POST "$API/api/v1/models/$MODEL_ID/execute" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
        "data_source": "splunk",
        "splunk_search": "index=proxy sourcetype=access_combined",
        "splunk_index": "proxy"
      }'
```

The search runs against the export endpoint and the result rows are handed to
the model as a DataFrame (numeric columns are coerced automatically). Searches
that don't start with `search` or a generating command (`|`) are prefixed with
`search` for you.

## Forwarding anomalies to Splunk

Enable **Forward anomalies to Splunk** in the integration config. After each
inference run, OpenUBA sends every anomaly to HEC as an `openuba:anomaly`
event in the configured `anomaly_index`. Forwarding is best-effort — a Splunk
outage never affects detection or persistence.

You can also forward events directly from Python:

```python
from core.integrations import SplunkConnector

splunk = SplunkConnector(hec_url="https://splunk:8088", hec_token="...")
splunk.send_anomaly({"entity_id": "u123", "risk_score": 0.97}, index="openuba")
```
