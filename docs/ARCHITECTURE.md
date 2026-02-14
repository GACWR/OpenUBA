# Architecture

OpenUBA v0.0.2 is a modular, Kubernetes-native User and Entity Behavior Analytics platform. This document describes the system architecture, data model, and component relationships.

## System Overview

```
                          +---------------------+
                          |   Next.js Frontend   |
                          |  (React / shadcn/ui) |
                          +----------+----------+
                                     |
                            REST / GraphQL / SSE
                                     |
                          +----------v----------+
                          |   FastAPI Backend    |
                          |   (Python 3.9)      |
                          +----+-----+-----+----+
                               |     |     |
              +----------------+     |     +----------------+
              |                      |                      |
   +----------v----------+  +-------v--------+  +----------v----------+
   |     PostgreSQL       |  |  PostGraphile  |  | Model Orchestrator  |
   |   (System of Record) |  | (GraphQL API)  |  |                     |
   +----------------------+  +----------------+  +----+--------+-------+
                                                      |        |
                                              +-------v--+ +---v---------+
                                              | Docker   | | Kubernetes  |
                                              | Driver   | | Job Driver  |
                                              +----+-----+ +------+------+
                                                   |              |
                                              +----v--------------v-----+
                                              |   Model Runner Containers |
                                              |   (Ephemeral Jobs)        |
                                              +---------------------------+

   Optional Compute Engines:
   +----------------+    +------------------+
   | Apache Spark   |    | Elasticsearch    |
   | (PySpark)      |    | + Kibana         |
   +----------------+    +------------------+
```

## Components

### Next.js Frontend

React-based web UI built with Next.js 14 (App Router), TypeScript, TailwindCSS, and shadcn/ui. Communicates with the backend via REST and GraphQL. Dark mode by default.

Pages:
- Home dashboard (KPI cards, risk trends, system status)
- Models (library, installed, jobs/runs, per-model detail)
- Anomalies (filterable table, detail drawer)
- Cases (incident management, linked anomalies)
- Rules (flow-based rule builder canvas, alerts)
- Data (ingestion status, source groups)
- Settings (integrations, user management)
- Display (entity risk visualization)
- LLM assistant (draggable overlay, multi-provider)

### FastAPI Backend

Python 3.9 application exposing 14 API routers:

| Router | Purpose |
|--------|---------|
| models | Model CRUD, install, train, execute |
| anomalies | Anomaly CRUD, acknowledge |
| cases | Case CRUD, link anomalies |
| rules | Rule CRUD, flow graph serialization |
| alerts | Alert listing, acknowledge |
| data | Data ingestion (Spark, Elasticsearch) |
| feedback | Analyst feedback on anomalies |
| display | Dashboard and entity display data |
| chat | LLM assistant (SSE streaming) |
| settings | Integration configuration |
| auth | Authentication, JWT tokens |
| notifications | User notification management |
| schedules | Model execution scheduling |
| source_groups | Data source group management |
| system | Health checks, system status |

The backend also manages:
- Database schema initialization (`core/db/init_schema.py`)
- PostGraphile subprocess for GraphQL
- Model orchestration (Docker or Kubernetes execution drivers)
- LLM chat dispatch (Ollama, OpenAI, Claude, Gemini)

### PostgreSQL Database

System of record. 20 tables:

**Core domain:**

| Table | Purpose |
|-------|---------|
| models | Model registry (slug, framework, runtime, manifest) |
| model_versions | Per-version metadata (source URI, code path, hashes) |
| model_components | Individual model files with integrity hashes |
| model_artifacts | Trained checkpoints (sklearn pickle, torch pt, tf saved model) |
| model_runs | Training and inference execution records |
| model_logs | Per-run structured log entries |

**Analytics:**

| Table | Purpose |
|-------|---------|
| anomalies | Detected anomalies (entity, risk score, model reference) |
| entities | User/entity profiles with aggregate risk |
| cases | Security incidents linked to anomalies |
| case_anomalies | Join table for cases and anomalies |
| rules | Detection rules with serialized flow graph (JSONB) |
| alerts | Alerts fired by rules |

**Platform:**

| Table | Purpose |
|-------|---------|
| users | System users with hashed passwords |
| role_permissions | RBAC matrix (role, page, read/write) |
| execution_logs | Container execution history |
| user_feedback | Analyst feedback on anomalies |
| notifications | User notification queue |
| audit_logs | Action audit trail |
| integration_settings | LLM and external service configuration |
| source_groups | Logical data source groupings |

### PostGraphile

Auto-generates a GraphQL API by introspecting the PostgreSQL schema. Provides queries, mutations, and subscriptions for all tables. Runs as a subprocess within the backend container, exposed on port 5001.

### Model Registry

Pluggable adapter system for discovering and fetching models from multiple sources:

```
core/registry/
  registry_service.py         # Unified interface
  adapters/
    code/
      local_fs.py             # Local filesystem
      github_code_adapter.py  # GitHub repositories
      hub_code_adapter.py     # OpenUBA Hub
    weights/
      local_fs_weights.py     # Local artifact files
      huggingface_adapter.py  # Hugging Face Hub
```

The model installer (`core/services/model_installer.py`) handles download, SHA-256 hash verification, manifest parsing, and database registration.

### Model Orchestrator

`core/services/model_orchestrator.py` dispatches model training and inference to isolated containers. Two execution drivers:

- **Kubernetes Job Driver** (production): Creates K8s Jobs via CRDs, operator watches and manages lifecycle.
- **Docker Driver** (development): Spawns containers via docker-py.

The orchestrator uses background daemon threads to avoid blocking the async event loop.

### OpenUBA Operator

Kopf-based Kubernetes controller (`core/operator/main.py`) that watches two custom resources:

**UBATraining** (`openuba.io/v1alpha1`):
- Spec: modelRef, runtime, configPath, outputPath, runId, modelSlug, modelVersion
- Status: phase (Pending/Running/Succeeded/Failed), startedAt, completedAt

**UBAInference** (`openuba.io/v1alpha1`):
- Spec: modelRef, runtime, inputPath, outputPath, runId, modelSlug, modelVersion, artifactPath
- Status: phase, resultReady, resultPath

For each CR, the operator creates a Kubernetes Job using the appropriate runtime image with four volume mounts:
1. `model-storage-pvc` at `/model` (read-write)
2. `system-storage-pvc` at `/system` (read-write, execution I/O)
3. `saved-models-pvc` at `/opt/openuba/saved_models` (trained artifacts)
4. `datasets-pvc` at `/app/test_datasets` (read-only)

Jobs have `backoffLimit: 0` (no retries) and `ttlSecondsAfterFinished: 300` (auto-cleanup).

### Model Runner

Ephemeral containers that execute model code in isolation. Framework-specific images built from a shared base:

| Image | Framework |
|-------|-----------|
| openuba-model-runner:base | Python 3.9 + PySpark + common deps |
| openuba-model-runner:sklearn | scikit-learn, joblib |
| openuba-model-runner:pytorch | PyTorch |
| openuba-model-runner:tensorflow | TensorFlow, Keras |
| openuba-model-runner:networkx | NetworkX graph analytics |

The runner (`docker/model-runner/runner.py`) handles:
- Hash verification of model code before execution
- Data loading via direct SQL (Postgres), HTTP (Elasticsearch), or Pandas CSV
- Framework-aware model serialization (joblib, torch.save, tf.saved_model)
- Result persistence to database

The runner has no dependency on the `core` package. It uses direct SQL via SQLAlchemy, direct HTTP via requests, and direct Pandas for CSV operations.

### Compute Engines (Optional)

**Apache Spark**: PySpark in local mode within runner containers. Reads CSV datasets directly via Spark CSV reader. CSV format varies by log type (tab-separated for ssh/dns/dhcp, space-separated with headers for proxy/bluecoat).

**Elasticsearch**: Stores indexed events and anomalies. Used for full-text search and Kibana dashboards. Connected via the Python elasticsearch client.

Both engines are optional. The system functions with just PostgreSQL.

## Kubernetes Deployment Topology

```
Namespace: openuba

Deployments:
  backend          (FastAPI + PostGraphile)
  frontend         (Next.js)
  operator         (Kopf CRD controller)
  postgres         (PostgreSQL 15)
  postgraphile     (GraphQL endpoint)
  spark-master     (Apache Spark master)
  spark-worker     (Apache Spark worker)
  elasticsearch    (Search/analytics)

Ephemeral Jobs:
  model-train-*    (Training runs, created by operator)
  model-infer-*    (Inference runs, created by operator)

PersistentVolumeClaims:
  source-code-pvc        -> /app/core (backend source)
  frontend-source-pvc    -> frontend source
  datasets-pvc           -> /app/test_datasets (immutable)
  saved-models-pvc       -> trained model artifacts
  system-storage-pvc     -> execution I/O
  metastore-pvc          -> Spark Derby metastore
  postgres-data-pvc      -> database files

CRDs:
  ubatrainings.openuba.io/v1alpha1
  ubainferences.openuba.io/v1alpha1
```

## Data Flow

### Model Training
```
POST /api/models/{id}/train
  -> Model Orchestrator (background thread)
  -> Write input config to system-storage-pvc
  -> Create UBATraining CR
  -> Operator creates K8s Job (runtime-specific image)
  -> Runner: verify hashes -> load data -> call train() -> save artifact
  -> Update model_runs, model_artifacts in Postgres
```

### Model Inference
```
POST /api/models/{id}/execute
  -> Model Orchestrator (background thread)
  -> Write input to system-storage-pvc
  -> Create UBAInference CR
  -> Operator creates K8s Job
  -> Runner: verify hashes -> load artifact -> load data -> call infer()
  -> Write anomalies to Postgres (+ optional Elasticsearch index)
  -> Update model_runs with result summary
```

### Data Ingestion
```
POST /api/v1/data/ingest
  -> DataIngestionService
  -> Read CSVs from test_datasets/toy_1/
  -> Ingest to Spark (create tables) and/or Elasticsearch (index documents)
```

## Security

- **Container isolation**: Each model runs in its own ephemeral container
- **Hash verification**: SHA-256 integrity checks on install and before every execution
- **RBAC**: Role-based access control (admin, analyst, viewer)
- **JWT authentication**: Token-based API auth with password hashing (bcrypt)
- **Read-only mounts**: Dataset volume mounted read-only in runner containers
- **Resource limits**: CPU/memory constraints on runner Jobs
- **Audit logging**: All actions recorded in audit_logs table
- **No root execution**: Runner containers use non-root modelrunner user (UID 1000)

## Local Development

The Kind cluster mounts the repository root at `/mnt/openuba/root` on the node, enabling all PersistentVolumes to reference host files directly. This is configured in `configs/local.yaml`.

Development workflow:
```
make reset-dev
```

This tears down any existing cluster and runs `scripts/start-dev.sh`, which creates a Kind cluster, builds all container images, loads them into the cluster, deploys all K8s resources, and opens terminal tabs for port forwarding, backend, and frontend.
