# OpenUBA Workspaces & Platform Enhancement: Implementation Plan

> **Branch:** `dev/workspaces`
> **Status:** Research Complete, Implementation Pending
> **Inspired By:** OpenModelStudio (OMS) — General-purpose AI experimentation lab
> **Philosophy:** OMS serves as the proving ground; battle-tested features graduate to OpenUBA's roadmap

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Architecture Vision](#3-architecture-vision)
4. [Core Abstractions](#4-core-abstractions)
5. [Phase 1: Workspace System](#5-phase-1-workspace-system)
6. [Phase 2: Enhanced `openuba` Python Package](#6-phase-2-enhanced-openuba-python-package)
7. [Phase 3: Jobs & Execution Engine](#7-phase-3-jobs--execution-engine)
8. [Phase 4: Visualization Framework](#8-phase-4-visualization-framework)
9. [Phase 5: Dashboard Framework](#9-phase-5-dashboard-framework)
10. [Phase 6: Feature Store & Experiment Tracking](#10-phase-6-feature-store--experiment-tracking)
11. [Phase 7: Pipeline System](#11-phase-7-pipeline-system)
12. [Phase 8: Frontend Integration](#12-phase-8-frontend-integration)
13. [Kubernetes CRD Strategy](#13-kubernetes-crd-strategy)
14. [Database Schema Additions](#14-database-schema-additions)
15. [API Endpoint Design](#15-api-endpoint-design)
16. [Security Considerations](#16-security-considerations)
17. [Testing Strategy](#17-testing-strategy)
18. [Migration & Compatibility](#18-migration--compatibility)
19. [OMS Feature Graduation Pipeline](#19-oms-feature-graduation-pipeline)
20. [Implementation Checklist](#20-implementation-checklist)

---

## 1. Executive Summary

### What We're Building

We are bringing OpenModelStudio's powerful experimentation capabilities into OpenUBA, adapted for the User Behavior Analytics domain. The core idea: **give security data scientists an interactive workspace inside OpenUBA where they can prototype anomaly detection models, create visualizations of security data, build custom dashboards, and run training/inference jobs — all powered by a swiss-army-knife `openuba` Python package.**

### The Four Core Abstractions

Every feature maps to one of four first-class platform nouns:

| Abstraction | What It Is | OpenUBA Domain Context |
|---|---|---|
| **Workspace** | Persistent, containerized environment (Jupyter) | Where analysts prototype UBA models |
| **Model** | Trainable/inferable ML artifact with lifecycle | Anomaly detectors, risk scorers, entity profilers |
| **Visualization** | Multi-backend rendered chart/graph | Risk heatmaps, anomaly timelines, entity graphs |
| **Dashboard** | Responsive grid of visualizations | SOC overview, entity risk profile, model performance |

### Why This Matters for OpenUBA

OpenUBA already has a model system, but it's "install and run." There's no way for a security data scientist to:
- Prototype a new anomaly detection model directly in the platform
- Iterate on hyperparameters and compare experiments
- Create custom visualizations of security telemetry
- Build operational dashboards for their SOC team
- Pull in datasets from Spark/ES/CSV within an interactive notebook
- Run distributed training jobs on Kubernetes

This plan brings all of that.

### Relationship to OpenModelStudio

```
┌─────────────────────────────────────────┐
│         OpenModelStudio (OMS)           │
│     General-purpose AI experiment lab   │
│  ┌───────────────────────────────────┐  │
│  │  Prove features here first        │  │
│  │  - Workspaces ✓                   │  │
│  │  - Viz framework ✓               │  │
│  │  - Dashboard framework ✓         │  │
│  │  - Jobs system ✓                 │  │
│  │  - Feature store ✓              │  │
│  │  - Experiment tracking ✓        │  │
│  │  - Pipelines ✓                  │  │
│  │  - Sweeps ✓                     │  │
│  └───────────────┬───────────────────┘  │
│                  │ Graduate             │
│                  ▼                      │
│  ┌───────────────────────────────────┐  │
│  │  When stable, add to OpenUBA     │  │
│  │  roadmap with UBA-domain         │  │
│  │  adaptations                      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│              OpenUBA                     │
│     User Behavior Analytics Platform    │
│  ┌───────────────────────────────────┐  │
│  │  Adapt for security domain:       │  │
│  │  - UBA-specific data sources     │  │
│  │  - Anomaly-aware visualizations  │  │
│  │  - Security rule integration     │  │
│  │  - Entity risk dashboards        │  │
│  │  - CRD-native K8s resources      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 2. Current State Analysis

### 2.1 OpenUBA Architecture (As-Is)

**Backend (`/core/`):**
- **Framework:** FastAPI 0.104.1 + Uvicorn
- **Database:** PostgreSQL via SQLAlchemy 2.0.23
- **Auth:** JWT (python-jose) + bcrypt (passlib) + RBAC (4 roles)
- **API Routers:** 14 modules (models, anomalies, cases, rules, alerts, data, entities, display, schedules, feedback, chat, users, health, graphql)
- **Services:** Model orchestrator, model installer, rule engine, data ingestion, chat service
- **Integrations:** Elasticsearch 8.11, PySpark 3.5, Ollama/OpenAI/Claude/Gemini
- **Operator:** Kopf-based K8s operator with UBATraining + UBAInference CRDs

**Frontend (`/interface/`):**
- **Framework:** Next.js 14 (App Router) + TypeScript
- **UI:** shadcn/ui (Radix primitives) + TailwindCSS
- **Data:** Apollo Client (GraphQL subscriptions) + Axios (REST)
- **State:** Zustand + Apollo cache
- **Special:** Rule canvas (@xyflow/react), Charts (Recharts), Command palette (cmdk)
- **Pages:** ~15 pages (home, models, anomalies, cases, rules, alerts, data, entities, settings, display, schedules)

**SDK (`/sdk/`):**
- **Package:** `openuba` (Python)
- **Commands:** install, uninstall, list, run, version
- **Client:** Registry cache (5-min TTL), local model management, offline-capable
- **Config:** `OPENUBA_API_URL`, `OPENUBA_TOKEN`, `OPENUBA_MODEL_DIR`, `OPENUBA_HUB_URL`

**Infrastructure:**
- **Docker:** 8 images (backend, frontend, operator, model-runner base + 4 framework variants)
- **K8s:** Full deployment (backend, frontend, postgres, spark, elasticsearch, postgraphile, operator)
- **PVCs:** source-code, frontend-source, datasets, saved-models, system-storage, model-storage, postgres-data, metastore
- **CRDs:** `ubatrainings.openuba.org`, `ubainferences.openuba.org`
- **RBAC:** backend-sa (create/read Jobs), operator-sa (CRUD CRDs)

**Model System:**
- Models live in `/core/model_library/{name}/`
- Each model has `MODEL.py` with `train(ctx)` and `infer(ctx)` interface
- Supported frameworks: scikit-learn, PyTorch, TensorFlow, NetworkX
- Model registry with adapters (local filesystem, GitHub, OpenUBA Hub)
- Hash verification (SHA-256) for installed models
- Docker/K8s execution modes

### 2.2 OpenModelStudio Architecture (Reference)

**Backend:** Rust/Axum, PostgreSQL/SQLx, S3 storage
**Frontend:** Next.js 16, shadcn/ui, react-grid-layout, Monaco editor
**SDK:** `openmodelstudio` Python package (1658-line client.py)
**K8s:** kube-rs for pod/job/PVC management, no CRDs (direct API)
**Key Features:**
- Workspaces (Jupyter pods with auto-configured SDK)
- 9-backend visualization framework
- Responsive dashboard framework (react-grid-layout)
- Jobs system (training/inference with hardware tiers)
- Feature store with transforms
- Experiment tracking with comparison
- Hyperparameter sweeps (random/grid search)
- Pipelines (multi-step workflows)
- Model versioning
- Real-time metric streaming (SSE)
- LLM assistant with tool execution

### 2.3 Gap Analysis

| Capability | OpenUBA | OMS | Gap |
|---|---|---|---|
| Model install from registry | Yes | Yes | None |
| Model training (K8s) | Yes (CRDs) | Yes (Jobs) | OpenUBA has CRDs (better) |
| Model inference (K8s) | Yes (CRDs) | Yes (Jobs) | OpenUBA has CRDs (better) |
| Interactive workspaces | **No** | Yes | **Critical gap** |
| SDK in workspace | **No** | Yes | **Critical gap** |
| Model creation in platform | **No** | Yes | **Critical gap** |
| Visualization framework | **No** | Yes (9 backends) | **Critical gap** |
| Dashboard framework | **No** | Yes (grid layout) | **Critical gap** |
| Feature store | **No** | Yes | **Gap** |
| Experiment tracking | **No** | Yes | **Gap** |
| Hyperparameter sweeps | **No** | Yes | **Gap** |
| Pipelines | **No** | Yes | **Gap** |
| Model versioning | Partial (git) | Yes (DB) | **Gap** |
| Real-time metrics | **No** | Yes (SSE) | **Gap** |
| Dataset management | Partial (Spark) | Yes (S3) | **Gap** |
| Framework auto-detection | **No** | Yes | **Gap** |
| Data source connectors | Yes (Spark, ES) | Yes (S3) | OpenUBA is richer |
| Rule engine | Yes | No | OpenUBA unique |
| Anomaly management | Yes | No | OpenUBA unique |
| Case management | Yes | No | OpenUBA unique |
| Entity risk scoring | Yes | No | OpenUBA unique |

---

## 3. Architecture Vision

### 3.1 Target Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OpenUBA Platform                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     Frontend (Next.js)                         │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │  │
│  │  │Models│ │Anom. │ │Rules │ │Work- │ │Dash- │ │Visualiz. │  │  │
│  │  │      │ │      │ │      │ │spaces│ │boards│ │          │  │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │  │
│  │  │Cases │ │Alerts│ │Data  │ │Exper.│ │Jobs  │ │Pipelines │  │  │
│  │  │      │ │      │ │      │ │      │ │      │ │          │  │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Backend (FastAPI)                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │
│  │  │ API Routers  │  │  Services    │  │  K8s Operator (Kopf) │ │  │
│  │  │ (20+ modules)│  │              │  │                      │ │  │
│  │  │              │  │ Orchestrator │  │  UBATraining CR      │ │  │
│  │  │ /models      │  │ Installer    │  │  UBAInference CR     │ │  │
│  │  │ /workspaces  │  │ RuleEngine   │  │  UBAWorkspace CR     │ │  │
│  │  │ /viz         │  │ DataIngest   │  │  UBAJob CR           │ │  │
│  │  │ /dashboards  │  │ WorkspaceMgr │  │  UBAPipeline CR      │ │  │
│  │  │ /jobs        │  │ VizService   │  │                      │ │  │
│  │  │ /experiments │  │ JobService   │  │  Watches CRs →       │ │  │
│  │  │ /features    │  │ ChatService  │  │  Creates K8s Jobs/   │ │  │
│  │  │ /pipelines   │  │              │  │  Pods/Services/PVCs  │ │  │
│  │  │ /sdk         │  │              │  │                      │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│              ┌───────────────┼──────────────────┐                    │
│              ▼               ▼                  ▼                    │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────────┐   │
│  │  PostgreSQL  │ │ Elasticsearch│ │     Kubernetes Cluster     │   │
│  │              │ │              │ │                            │   │
│  │ models       │ │ security     │ │ ┌────────────────────────┐ │   │
│  │ workspaces   │ │ telemetry    │ │ │  Workspace Pods        │ │   │
│  │ visualiz.    │ │ indices      │ │ │  (Jupyter + openuba)   │ │   │
│  │ dashboards   │ │              │ │ ├────────────────────────┤ │   │
│  │ experiments  │ │              │ │ │  Training Jobs         │ │   │
│  │ features     │ │              │ │ │  (model-runner pods)   │ │   │
│  │ jobs         │ │              │ │ ├────────────────────────┤ │   │
│  │ pipelines    │ │              │ │ │  Inference Jobs        │ │   │
│  │ ...          │ │              │ │ │  (model-runner pods)   │ │   │
│  └──────────────┘ └──────────────┘ │ └────────────────────────┘ │   │
│                                    └────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              openuba Python Package (SDK)                      │  │
│  │                                                                │  │
│  │  Used in: Workspace notebooks, CLI, external scripts          │  │
│  │                                                                │  │
│  │  openuba.register_model()    openuba.create_visualization()   │  │
│  │  openuba.start_training()    openuba.create_dashboard()       │  │
│  │  openuba.start_inference()   openuba.load_dataset()           │  │
│  │  openuba.load_features()     openuba.create_experiment()      │  │
│  │  openuba.run_pipeline()      openuba.stream_metrics()         │  │
│  │  openuba.query_anomalies()   openuba.get_entity_risk()        │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Design Principles

1. **CRD-Native**: Unlike OMS which uses direct K8s API calls, OpenUBA will define CRDs for every orchestrated resource (workspaces, jobs, pipelines). The Kopf operator watches CRs and manages the underlying K8s resources. This gives us declarative, auditable, reconcilable infrastructure.

2. **Domain-Aware Abstractions**: Every feature is adapted for the UBA/security domain. Visualizations aren't just charts — they're anomaly timelines, entity risk heatmaps, network graphs. Dashboards aren't just grids — they're SOC overviews.

3. **SDK-First Design**: The `openuba` Python package is the primary interface for data scientists. Everything that can be done in the UI can be done from a notebook. The SDK auto-configures itself in workspace pods via environment variables.

4. **Backward Compatibility**: All existing model, anomaly, case, rule, and alert systems remain untouched. New features are additive.

5. **Extensible by Design**: New visualization backends, new workspace types, new data source connectors, new model frameworks — all pluggable via adapter patterns.

---

## 4. Core Abstractions

### 4.1 Workspace

A **Workspace** is a persistent, containerized environment where security data scientists can interactively prototype and develop UBA capabilities.

```
┌─────────────────────────────────────────┐
│  UBAWorkspace CRD                       │
│                                         │
│  spec:                                  │
│    name: "jdoe-anomaly-research"        │
│    project_id: "uuid"                   │
│    environment: "jupyter-sklearn"       │
│    hardware_tier: "cpu-small"           │
│    ide: "jupyterlab"                    │
│                                         │
│  status:                                │
│    phase: Running                       │
│    pod_name: "uba-ws-uuid"             │
│    access_url: "http://localhost:31100" │
│    pvc_name: "uba-ws-uuid-data"        │
│    created_at: "2026-03-14T..."        │
└─────────────────────────────────────────┘
         │
         │ Operator creates:
         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Pod         │  │  Service     │  │  PVC         │
│  (Jupyter)   │  │  (NodePort)  │  │  (5Gi)       │
│              │  │              │  │              │
│  ENV:        │  │  31100-31199 │  │  /workspace  │
│  OPENUBA_*   │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Lifecycle:** Create → Running → Stopped → Deleted
**Persistence:** PVC mounted at `/workspace` survives pod restarts
**SDK:** `openuba` package pre-installed, auto-configured via env vars
**Data Access:** Can query Spark tables, Elasticsearch indices, CSV datasets

### 4.2 Model (Enhanced)

The existing model system is extended with:
- **In-platform creation** (register from notebook via SDK)
- **Framework auto-detection** (sklearn, PyTorch, TensorFlow, NetworkX)
- **Model serialization** (pickle/torch.save/keras.save → base64 embedding)
- **Model versioning** (DB-tracked versions with source code archive)
- **Remote training** (K8s Job via UBATraining CRD)
- **Remote inference** (K8s Job via UBAInference CRD)

```python
# In a workspace notebook:
import openuba
from sklearn.ensemble import IsolationForest

# Create model
clf = IsolationForest(n_estimators=100, contamination=0.1)

# Register with auto-detection
handle = openuba.register_model(
    "ssh-anomaly-detector",
    model=clf,
    description="Detects anomalous SSH sessions"
)

# Train remotely on K8s
job = openuba.start_training(
    handle.model_id,
    dataset_id="ssh-logs-2026",
    hyperparameters={"n_estimators": 200, "contamination": 0.05},
    hardware_tier="cpu-large",
    wait=True
)

# Check results
print(job["status"])  # "completed"
logs = openuba.get_logs(job["id"])
```

### 4.3 Visualization

A **Visualization** is a multi-backend rendered chart, graph, or map that can be created from the SDK or UI.

```python
# In a workspace notebook:
import openuba
import matplotlib.pyplot as plt

# Create a risk score distribution
fig, ax = plt.subplots(figsize=(10, 6))
risk_scores = openuba.query_anomalies(fields=["risk_score"])
ax.hist(risk_scores, bins=50, color='#ff6b6b', alpha=0.7)
ax.set_title("Entity Risk Score Distribution")
ax.set_xlabel("Risk Score")

# Register and render
viz = openuba.create_visualization(
    "risk-distribution",
    backend="matplotlib",
    description="Distribution of entity risk scores"
)
openuba.render(fig, viz_id=viz["id"])
openuba.publish_visualization(viz["id"])
```

**Supported Backends (9):**
1. matplotlib (SVG)
2. seaborn (SVG — statistical)
3. plotly (interactive JSON)
4. bokeh (interactive JSON)
5. altair (Vega-Lite JSON — declarative)
6. plotnine (SVG — ggplot2-style)
7. datashader (PNG — millions of points)
8. networkx (SVG — entity relationship graphs)
9. geopandas (SVG — geographic maps)

### 4.4 Dashboard

A **Dashboard** is a responsive, 12-column grid layout that composes multiple visualizations into an operational view.

```python
# In a workspace notebook:
import openuba

# Create dashboard
dashboard = openuba.create_dashboard(
    "SOC Overview",
    layout=[
        {"visualization_id": risk_dist["id"], "x": 0, "y": 0, "w": 6, "h": 2},
        {"visualization_id": timeline["id"], "x": 6, "y": 0, "w": 6, "h": 2},
        {"visualization_id": entity_graph["id"], "x": 0, "y": 2, "w": 12, "h": 3},
    ],
    description="Security operations center overview dashboard"
)
```

**Features:**
- Drag-and-drop panel arrangement
- Resize panels
- Lock/unlock toggle
- Responsive breakpoints (lg/md/sm/xs/xxs)
- Lazy-loading with IntersectionObserver
- Auto-refresh interval per visualization
- Export individual panels

---

## 5. Phase 1: Workspace System

### 5.1 Overview

The workspace system is the foundation that enables all other features. Without workspaces, data scientists can't use the SDK interactively.

### 5.2 UBAWorkspace CRD

**File:** `k8s/crds/ubaworkspace-crd.yaml`

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: ubaworkspaces.openuba.org
spec:
  group: openuba.org
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [name, created_by]
              properties:
                name:
                  type: string
                project_id:
                  type: string
                environment:
                  type: string
                  default: "default"
                hardware_tier:
                  type: string
                  enum: [cpu-small, cpu-large, gpu-small, gpu-large]
                  default: cpu-small
                ide:
                  type: string
                  enum: [jupyterlab]
                  default: jupyterlab
                created_by:
                  type: string
                timeout_hours:
                  type: integer
                  default: 24
            status:
              type: object
              properties:
                phase:
                  type: string
                  enum: [Pending, Creating, Running, Stopping, Stopped, Failed, Deleting]
                pod_name:
                  type: string
                service_name:
                  type: string
                pvc_name:
                  type: string
                access_url:
                  type: string
                node_port:
                  type: integer
                started_at:
                  type: string
                message:
                  type: string
      subresources:
        status: {}
      additionalPrinterColumns:
        - name: Status
          type: string
          jsonPath: .status.phase
        - name: URL
          type: string
          jsonPath: .status.access_url
        - name: Tier
          type: string
          jsonPath: .spec.hardware_tier
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
  scope: Namespaced
  names:
    plural: ubaworkspaces
    singular: ubaworkspace
    kind: UBAWorkspace
    shortNames: [ubaws]
```

### 5.3 Operator Handler

**File:** `core/operator/workspace_handler.py`

The Kopf operator watches UBAWorkspace CRs and manages:

1. **on.create** → Create PVC + Pod + Service
2. **on.update** → Handle spec changes (hardware tier, environment)
3. **on.delete** → Cleanup PVC + Pod + Service
4. **on.timer** → Check pod health, enforce timeout

**Pod Creation Details:**
- Image: `openuba-workspace:latest` (custom Jupyter image with `openuba` pre-installed)
- Volume mount: PVC at `/workspace`
- Environment variables:
  ```
  OPENUBA_API_URL=http://backend.openuba.svc:8000
  OPENUBA_TOKEN=<workspace-jwt-30-day>
  OPENUBA_WORKSPACE_ID=<uuid>
  OPENUBA_PROJECT_ID=<uuid>
  JUPYTER_ENABLE_LAB=yes
  ```
- Resource limits per hardware tier:
  ```
  cpu-small:  requests={cpu: 250m, memory: 512Mi}  limits={cpu: 500m, memory: 1Gi}
  cpu-large:  requests={cpu: 500m, memory: 2Gi}    limits={cpu: 2, memory: 4Gi}
  gpu-small:  requests={cpu: 500m, memory: 1Gi}    limits={cpu: 2, memory: 4Gi, gpu: 1}
  gpu-large:  requests={cpu: 1, memory: 2Gi}       limits={cpu: 4, memory: 8Gi, gpu: 4}
  ```

**Service Creation:**
- Type: NodePort
- Port range: 31100-31199 (dynamically allocated)
- Target port: 8888 (Jupyter)

### 5.4 Workspace Docker Image

**File:** `docker/workspace/Dockerfile`

```dockerfile
FROM jupyter/scipy-notebook:latest

USER root

# Install openuba SDK
COPY sdk/src/openuba /tmp/openuba-sdk/openuba
COPY sdk/pyproject.toml /tmp/openuba-sdk/
RUN pip install /tmp/openuba-sdk/

# Install visualization libraries
RUN pip install \
    matplotlib \
    seaborn \
    plotly \
    bokeh \
    altair \
    plotnine \
    datashader \
    networkx \
    geopandas

# Install ML frameworks
RUN pip install \
    scikit-learn \
    torch \
    tensorflow

# Install data connectors
RUN pip install \
    pyspark \
    elasticsearch \
    psycopg2-binary \
    requests

# Welcome notebook
COPY workspace/welcome.ipynb /home/jovyan/work/

USER jovyan
```

### 5.5 Backend API

**File:** `core/api_routers/workspaces.py`

```
POST   /api/v1/workspaces/launch        → Create UBAWorkspace CR
GET    /api/v1/workspaces               → List workspaces
GET    /api/v1/workspaces/{id}          → Get workspace details
DELETE /api/v1/workspaces/{id}          → Delete UBAWorkspace CR
POST   /api/v1/workspaces/{id}/stop     → Stop workspace (delete pod, keep PVC)
POST   /api/v1/workspaces/{id}/restart  → Restart workspace (recreate pod)
```

### 5.6 Database Model

```python
class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    environment = Column(String, default="default")
    hardware_tier = Column(String, default="cpu-small")
    ide = Column(String, default="jupyterlab")
    status = Column(String, default="pending")  # pending, running, stopped, failed
    pod_name = Column(String, nullable=True)
    service_name = Column(String, nullable=True)
    pvc_name = Column(String, nullable=True)
    access_url = Column(String, nullable=True)
    node_port = Column(Integer, nullable=True)
    cr_name = Column(String, nullable=True)  # UBAWorkspace CR name
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    timeout_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 5.7 Implementation Checklist

- [ ] Create UBAWorkspace CRD YAML
- [ ] Implement Kopf operator handler for UBAWorkspace
- [ ] Build workspace Docker image
- [ ] Create workspace API router
- [ ] Create workspace database model + migration
- [ ] Create workspace repository
- [ ] Create workspace service
- [ ] Add workspace JWT token generation (30-day expiry)
- [ ] Implement NodePort allocation (31100-31199)
- [ ] Create welcome.ipynb notebook
- [ ] Add workspace page to frontend
- [ ] Add workspace to sidebar navigation
- [ ] Add Makefile targets for building workspace image
- [ ] Write unit tests for workspace API
- [ ] Write integration tests for workspace lifecycle
- [ ] Add workspace environment management (custom images)

---

## 6. Phase 2: Enhanced `openuba` Python Package

### 6.1 Overview

Transform the existing `openuba` SDK from a simple "install/run" CLI into a comprehensive swiss-army-knife package. This is modeled after the OMS Python SDK but adapted for UBA.

### 6.2 Current SDK vs. Target SDK

**Current (`sdk/src/openuba/`):**
```python
# Current capabilities (limited)
openuba.install("model_sklearn")
openuba.uninstall("model_sklearn")
openuba.run("model_sklearn", data="path/to/data.csv")
openuba.list_models()
openuba.list_installed()
```

**Target:**
```python
import openuba

# ─── Configuration (auto from env vars in workspaces) ───
openuba.configure(api_url="http://localhost:8000", token="...")

# ─── Model Management ───
handle = openuba.register_model("my-model", model=clf)
openuba.publish_version(handle.model_id, summary="improved accuracy")
clf = openuba.load_model("my-model")
registry_model = openuba.use_model("isolation-forest-v2")
openuba.install("model_sklearn")
openuba.uninstall("model_sklearn")

# ─── Dataset Management ───
datasets = openuba.list_datasets()
df = openuba.load_dataset("ssh-logs-2026")
openuba.create_dataset("processed-logs", df)

# ─── Data Source Access (UBA-specific) ───
df = openuba.query_spark("SELECT * FROM ssh_logs WHERE risk > 0.7")
df = openuba.query_elasticsearch("ssh-*", {"query": {"range": {"risk_score": {"gte": 0.8}}}})
anomalies = openuba.query_anomalies(entity_id="jdoe", min_risk=0.7)
entity = openuba.get_entity_risk("jdoe")

# ─── Feature Store ───
openuba.create_features(df, feature_names=["login_count", "avg_session"], group_name="ssh-v1")
df = openuba.load_features("ssh-v1", df=df)

# ─── Hyperparameters ───
openuba.create_hyperparameters("rf-tuned", {"n_estimators": 200, "max_depth": 10})
params = openuba.load_hyperparameters("rf-tuned")

# ─── Training & Inference ───
job = openuba.start_training(model_id, dataset_id="ssh-logs", hardware_tier="gpu-small", wait=True)
job = openuba.start_inference(model_id, input_data={"features": [1, 2, 3]})
openuba.get_job(job["id"])
openuba.wait_for_job(job["id"])
openuba.stream_metrics(job["id"], callback=lambda m: print(m))

# ─── Experiments ───
exp = openuba.create_experiment("contamination-sweep")
openuba.add_experiment_run(exp["id"], job_id=job["id"], parameters={"contamination": 0.1})
comparison = openuba.compare_experiment_runs(exp["id"])

# ─── Visualizations ───
viz = openuba.create_visualization("risk-heatmap", backend="plotly")
openuba.render(fig, viz_id=viz["id"])
openuba.publish_visualization(viz["id"])

# ─── Dashboards ───
dash = openuba.create_dashboard("SOC Overview", layout=[...])
openuba.update_dashboard(dash["id"], layout=[...])

# ─── Pipelines ───
pipe = openuba.create_pipeline("daily-anomaly-scan", steps=[...])
openuba.run_pipeline(pipe["id"], wait=True)

# ─── Logging ───
openuba.post_log(job["id"], "Training started", level="info")
logs = openuba.get_logs(job["id"])
```

### 6.3 Package Structure

```
sdk/src/openuba/
├── __init__.py              # Re-exports all public functions
├── __main__.py              # python -m openuba → cli.main()
├── client.py                # OpenUBAClient — main API client class
├── model.py                 # Module-level convenience functions (singleton pattern)
├── visualization.py         # VisualizationContext + 9 backend renderers
├── registry.py              # Registry search/install/uninstall
├── config.py                # Configuration + project root detection
├── cli.py                   # Click CLI commands (enhanced)
└── context.py               # ModelContext for train/infer (used by runner)
```

### 6.4 Client Class Design

**Pattern:** Singleton client, auto-configured from environment variables

```python
class OpenUBAClient:
    def __init__(self, api_url=None, token=None):
        self.api_url = api_url or os.environ.get("OPENUBA_API_URL", "http://localhost:8000")
        self.token = token or os.environ.get("OPENUBA_TOKEN")
        self.workspace_id = os.environ.get("OPENUBA_WORKSPACE_ID")
        self.project_id = os.environ.get("OPENUBA_PROJECT_ID")

    # ─── HTTP helpers ───
    def _headers(self): ...
    def _get(self, path, params=None): ...
    def _post(self, path, body): ...
    def _put(self, path, body): ...
    def _delete(self, path): ...

    # ─── Model Management ───
    def register_model(self, name, model=None, framework=None, ...): ...
    def load_model(self, name_or_id, version=None): ...
    def use_model(self, registry_name): ...
    # ... (see full API in §6.2)

    # ─── Framework Detection ───
    @staticmethod
    def _detect_framework(model): ...
    @staticmethod
    def _serialize_model(model, framework): ...
    @staticmethod
    def _generate_source_code(framework, model_b64): ...
```

### 6.5 UBA-Specific SDK Methods

These are unique to OpenUBA and don't exist in OMS:

```python
# Query anomalies from the platform
def query_anomalies(entity_id=None, model_id=None, min_risk=None,
                    max_risk=None, start_time=None, end_time=None,
                    limit=1000, fields=None) -> pd.DataFrame:
    """Query anomalies with filters, returns DataFrame"""

# Get entity risk profile
def get_entity_risk(entity_id) -> dict:
    """Returns entity risk score, anomaly count, recent activity"""

# Query cases
def query_cases(status=None, severity=None, limit=100) -> pd.DataFrame:
    """Query security cases"""

# Query Spark tables directly
def query_spark(sql) -> pd.DataFrame:
    """Execute Spark SQL query, return DataFrame"""

# Query Elasticsearch indices
def query_elasticsearch(index, query_body) -> pd.DataFrame:
    """Execute ES query, return DataFrame"""

# Get rules and their evaluation history
def list_rules(enabled=True) -> list:
    """List detection rules"""

# Evaluate a rule against anomaly data
def evaluate_rule(rule_id, anomaly_data) -> dict:
    """Test rule evaluation"""
```

### 6.6 Visualization Module

Adapted from OMS with identical 9-backend support. Key differences:
- Uses OpenUBA API endpoints (`/api/v1/visualizations` vs `/sdk/visualizations`)
- Includes UBA-specific chart templates (risk distribution, entity timeline, etc.)

### 6.7 Implementation Checklist

- [ ] Refactor `sdk/src/openuba/client.py` with full API client
- [ ] Add `sdk/src/openuba/visualization.py` (9 backends)
- [ ] Add `sdk/src/openuba/context.py` (ModelContext for runners)
- [ ] Enhance `sdk/src/openuba/model.py` with singleton convenience functions
- [ ] Enhance `sdk/src/openuba/registry.py` with platform API integration
- [ ] Enhance `sdk/src/openuba/config.py` with project root detection
- [ ] Enhance `sdk/src/openuba/cli.py` with new commands
- [ ] Update `sdk/src/openuba/__init__.py` with all exports
- [ ] Add framework auto-detection (sklearn, PyTorch, TF, NetworkX)
- [ ] Add model serialization (pickle, torch.save, keras.save)
- [ ] Add source code generation with embedded model
- [ ] Add UBA-specific query methods (anomalies, entities, Spark, ES)
- [ ] Add `sdk/pyproject.toml` dependencies (requests, pandas, numpy)
- [ ] Write comprehensive unit tests
- [ ] Write integration tests with mock API
- [ ] Create example notebooks for each capability
- [ ] Update SDK documentation

---

## 7. Phase 3: Jobs & Execution Engine

### 7.1 Overview

Enhance the existing CRD-based execution system with:
- Hardware tier support
- Real-time metric streaming
- Job logging
- Progress tracking
- SDK-initiated jobs

### 7.2 Enhanced UBATraining CRD

The existing UBATraining CRD needs these additions:

```yaml
spec:
  # Existing
  model_name: "ssh-anomaly-detector"
  data_source: "spark"
  table_name: "ssh_logs"

  # New fields
  model_id: "uuid"           # DB model ID (for SDK-registered models)
  dataset_id: "uuid"         # DB dataset ID
  hardware_tier: "cpu-small"  # Resource allocation
  hyperparameters:            # JSON training params
    n_estimators: 200
    contamination: 0.05
  experiment_id: "uuid"       # Link to experiment
  source_code: "..."          # Inline model code (for SDK-registered models)

status:
  # Existing
  phase: Running

  # New fields
  progress: 45               # 0-100
  epoch_current: 5
  epoch_total: 10
  loss: 0.234
  learning_rate: 0.001
  metrics_endpoint: "http://backend:8000/api/v1/internal/metrics"
  started_at: "2026-03-14T..."
  completed_at: "2026-03-14T..."
  error_message: ""
```

### 7.3 Job Database Model

```python
class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    model_id = Column(UUID, ForeignKey("models.id"), nullable=False)
    dataset_id = Column(UUID, nullable=True)
    job_type = Column(String, nullable=False)  # "training" or "inference"
    status = Column(String, default="pending")
    cr_name = Column(String, nullable=True)  # UBATraining/UBAInference CR name
    k8s_job_name = Column(String, nullable=True)
    hardware_tier = Column(String, default="cpu-small")
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)  # Final aggregated metrics
    progress = Column(Integer, default=0)
    epoch_current = Column(Integer, nullable=True)
    epoch_total = Column(Integer, nullable=True)
    loss = Column(Float, nullable=True)
    learning_rate = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 7.4 Metrics Streaming

**Internal endpoint for runner pods:**
```
POST /api/v1/internal/metrics/{job_id}
Body: {"metric_name": "loss", "value": 0.234, "epoch": 5, "step": 100}
```

**SSE endpoint for clients:**
```
GET /api/v1/jobs/{job_id}/metrics/stream
→ Server-Sent Events with real-time metric updates
```

**Implementation:**
- Use `asyncio.Queue` per active job for in-memory buffering
- Runner pods POST metrics every 2 seconds
- API broadcasts to connected SSE clients
- Metrics also stored in `training_metrics` table for history

### 7.5 Job Logging

```python
class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(UUID, primary_key=True, default=uuid4)
    job_id = Column(UUID, ForeignKey("jobs.id"), nullable=False)
    level = Column(String, default="info")  # info, warning, error, debug
    message = Column(String, nullable=False)
    logger_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
```

### 7.6 Enhanced Model Runner

**File:** `docker/model-runner/runner.py`

The runner already exists but needs enhancements:
- Support for SDK-registered models (fetch source_code from DB)
- MetricReporter (buffered HTTP POST every 2 seconds)
- ModelLogHandler (batched log posting)
- ModelContext with methods: `log_metric()`, `save_artifact()`, `get_input_data()`, `set_output()`

### 7.7 Implementation Checklist

- [ ] Enhance UBATraining CRD with new fields
- [ ] Enhance UBAInference CRD with new fields
- [ ] Create Job database model + migration
- [ ] Create JobLog database model
- [ ] Create TrainingMetric database model
- [ ] Create job API router (`/api/v1/jobs`)
- [ ] Create internal metrics endpoint (`/api/v1/internal/metrics/{job_id}`)
- [ ] Create internal logs endpoint (`/api/v1/internal/logs/{job_id}`)
- [ ] Implement SSE metrics streaming
- [ ] Update Kopf operator for new CRD fields
- [ ] Update model runner with MetricReporter
- [ ] Update model runner with ModelLogHandler
- [ ] Update model runner with ModelContext enhancements
- [ ] Add SDK start_training/start_inference methods
- [ ] Add SDK get_job/wait_for_job/stream_metrics methods
- [ ] Write tests for job lifecycle
- [ ] Write tests for metrics streaming

---

## 8. Phase 4: Visualization Framework

### 8.1 Overview

Port the OMS 9-backend visualization framework to OpenUBA, adding UBA-specific visualization templates.

### 8.2 Backend Visualization Model

```python
class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    backend = Column(String, nullable=False)  # matplotlib, plotly, bokeh, etc.
    output_type = Column(String, nullable=False)  # svg, plotly, bokeh, vega-lite, png
    code = Column(Text, nullable=True)  # Python render(ctx) function
    data = Column(JSON, nullable=True)  # Data payload
    config = Column(JSON, nullable=True)  # {width, height, theme, ...}
    rendered_output = Column(Text, nullable=True)  # Cached rendered output
    refresh_interval = Column(Integer, default=0)  # 0=static, >0=auto-refresh seconds
    published = Column(Boolean, default=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 8.3 API Endpoints

```
POST   /api/v1/visualizations                    → Create visualization
GET    /api/v1/visualizations                    → List visualizations
GET    /api/v1/visualizations/{id}               → Get visualization (with rendered output)
PUT    /api/v1/visualizations/{id}               → Update visualization (rendered output)
DELETE /api/v1/visualizations/{id}               → Delete visualization
POST   /api/v1/visualizations/{id}/publish       → Publish visualization
POST   /api/v1/visualizations/{id}/render        → Server-side render + cache
```

### 8.4 Frontend VizRenderer Component

Port the OMS `VizRenderer` component:
- SVG rendering (inline, sanitized)
- PNG rendering (base64 image)
- Plotly.js rendering (CDN-loaded, dark theme)
- Vega-Lite rendering (CDN-loaded)
- Bokeh rendering (CDN-loaded)
- Download/export functionality

### 8.5 UBA-Specific Visualization Templates

Pre-built templates for common UBA visualizations:

1. **Risk Score Distribution** (matplotlib) — Histogram of entity risk scores
2. **Anomaly Timeline** (plotly) — Interactive scatter of anomalies over time
3. **Entity Risk Heatmap** (seaborn) — Heatmap of entity risk by category
4. **Network Graph** (networkx) — Entity relationship graph
5. **Geo IP Map** (geopandas) — Geographic distribution of login locations
6. **Model Performance** (plotly) — ROC curve, precision-recall, confusion matrix
7. **Feature Importance** (matplotlib) — Bar chart of feature importances
8. **Alert Volume** (altair) — Stacked bar of alerts by severity over time
9. **Session Pattern** (bokeh) — Interactive session timeline per entity
10. **Large-Scale Scatter** (datashader) — Millions of log entries by time/risk

### 8.6 Implementation Checklist

- [ ] Create Visualization database model + migration
- [ ] Create visualization API router
- [ ] Port `visualization.py` to `sdk/src/openuba/visualization.py`
- [ ] Port `VizRenderer` component to frontend
- [ ] Create visualization list page (`/visualizations`)
- [ ] Create visualization editor page (`/visualizations/[id]`)
- [ ] Add Monaco editor integration for code editing
- [ ] Add backend template code for all 9 backends
- [ ] Create 10 UBA-specific visualization templates
- [ ] Add visualization to sidebar navigation
- [ ] Write unit tests
- [ ] Write integration tests

---

## 9. Phase 5: Dashboard Framework

### 9.1 Overview

Port the OMS responsive dashboard framework to OpenUBA.

### 9.2 Backend Dashboard Model

```python
class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    layout = Column(JSON, default=[])  # Array of {visualization_id, x, y, w, h}
    published = Column(Boolean, default=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 9.3 API Endpoints

```
POST   /api/v1/dashboards              → Create dashboard
GET    /api/v1/dashboards              → List dashboards
GET    /api/v1/dashboards/{id}         → Get dashboard (with layout)
PUT    /api/v1/dashboards/{id}         → Update dashboard (layout, name)
DELETE /api/v1/dashboards/{id}         → Delete dashboard
```

### 9.4 Frontend Dashboard Components

**Dependencies:**
- `react-grid-layout` — Drag-and-drop grid
- `VizRenderer` — Universal visualization renderer (from Phase 4)

**Dashboard Editor Features:**
- 12-column responsive grid (breakpoints: lg/md/sm/xs/xxs)
- ROW_HEIGHT: 120px
- Drag-and-drop panel rearrangement (via `.drag-handle`)
- Panel resize by corner
- Lock/unlock toggle
- Add panel dialog (select visualization, choose dimensions)
- Remove panel
- LazyVizPanel (IntersectionObserver for performance)
- Panel header: name, backend badge, download, expand, delete
- Save button
- Auto-compaction (vertical)

### 9.5 Pre-Built Dashboard Templates

1. **SOC Overview** — Alert volume, risk distribution, recent anomalies, entity leaderboard
2. **Entity Risk Profile** — Entity details, anomaly timeline, session patterns, risk trend
3. **Model Performance** — ROC curve, confusion matrix, feature importance, training loss
4. **Data Source Health** — Ingestion rates, error counts, latency, coverage

### 9.6 Implementation Checklist

- [ ] Create Dashboard database model + migration
- [ ] Create dashboard API router
- [ ] Add `react-grid-layout` to frontend dependencies
- [ ] Create dashboard list page (`/dashboards`)
- [ ] Create dashboard editor page (`/dashboards/[id]`)
- [ ] Implement LazyVizPanel with IntersectionObserver
- [ ] Implement panel add/remove/resize/drag
- [ ] Implement lock/unlock toggle
- [ ] Implement responsive breakpoints
- [ ] Implement panel download/export
- [ ] Create pre-built dashboard templates
- [ ] Add dashboard to sidebar navigation
- [ ] Add SDK dashboard methods
- [ ] Write tests

---

## 10. Phase 6: Feature Store & Experiment Tracking

### 10.1 Feature Store

**Database Models:**
```python
class FeatureGroup(Base):
    __tablename__ = "feature_groups"
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, nullable=True)
    name = Column(String, nullable=False)
    entity = Column(String, default="default")
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Feature(Base):
    __tablename__ = "features"
    id = Column(UUID, primary_key=True, default=uuid4)
    group_id = Column(UUID, ForeignKey("feature_groups.id"), nullable=False)
    name = Column(String, nullable=False)
    dtype = Column(String)  # float, int, string
    mean = Column(Float, nullable=True)
    std = Column(Float, nullable=True)
    min_val = Column(Float, nullable=True)
    max_val = Column(Float, nullable=True)
    null_rate = Column(Float, nullable=True)
    transform = Column(String, nullable=True)  # standard_scaler, min_max_scaler, log_transform, one_hot
    transform_params = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
```

**SDK Methods:**
```python
openuba.create_features(df, feature_names=["f1", "f2"], group_name="ssh-v1", transforms=["standard_scaler"])
df = openuba.load_features("ssh-v1", df=raw_df)  # Applies stored transforms
```

### 10.2 Experiment Tracking

**Database Models:**
```python
class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())

class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    id = Column(UUID, primary_key=True, default=uuid4)
    experiment_id = Column(UUID, ForeignKey("experiments.id"), nullable=False)
    job_id = Column(UUID, ForeignKey("jobs.id"), nullable=True)
    model_id = Column(UUID, ForeignKey("models.id"), nullable=True)
    parameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### 10.3 Hyperparameter Store

```python
class HyperparameterSet(Base):
    __tablename__ = "hyperparameter_sets"
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, nullable=True)
    name = Column(String, nullable=False)
    model_id = Column(UUID, nullable=True)
    parameters = Column(JSON, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### 10.4 Implementation Checklist

- [ ] Create FeatureGroup + Feature database models + migration
- [ ] Create Experiment + ExperimentRun database models + migration
- [ ] Create HyperparameterSet database model + migration
- [ ] Create feature store API router (`/api/v1/features`)
- [ ] Create experiments API router (`/api/v1/experiments`)
- [ ] Create hyperparameters API router (`/api/v1/hyperparameters`)
- [ ] Add SDK methods for features, experiments, hyperparameters
- [ ] Create frontend pages: `/features`, `/experiments`, `/hyperparameters`
- [ ] Add experiment comparison view (parallel coordinates chart)
- [ ] Write tests

---

## 11. Phase 7: Pipeline System

### 11.1 Overview

Pipelines are multi-step workflows that chain data processing, training, inference, and other operations.

### 11.2 UBAPipeline CRD

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: ubapipelines.openuba.org
spec:
  group: openuba.org
  names:
    plural: ubapipelines
    singular: ubapipeline
    kind: UBAPipeline
    shortNames: [ubapipe]
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                name:
                  type: string
                steps:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                        enum: [training, inference, data_processing]
                      model_id:
                        type: string
                      dataset_id:
                        type: string
                      hyperparameters:
                        type: object
                        x-kubernetes-preserve-unknown-fields: true
                      hardware_tier:
                        type: string
            status:
              type: object
              properties:
                phase:
                  type: string
                current_step:
                  type: integer
                step_statuses:
                  type: array
                  items:
                    type: object
                    properties:
                      step_index:
                        type: integer
                      status:
                        type: string
                      job_id:
                        type: string
```

### 11.3 Database Models

```python
class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    steps = Column(JSON, nullable=False)  # Array of step definitions
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(UUID, primary_key=True, default=uuid4)
    pipeline_id = Column(UUID, ForeignKey("pipelines.id"), nullable=False)
    status = Column(String, default="pending")
    current_step = Column(Integer, default=0)
    step_statuses = Column(JSON, default=[])
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### 11.4 Implementation Checklist

- [ ] Create UBAPipeline CRD
- [ ] Implement Kopf operator handler for UBAPipeline
- [ ] Create Pipeline + PipelineRun database models + migration
- [ ] Create pipeline API router (`/api/v1/pipelines`)
- [ ] Add SDK pipeline methods
- [ ] Create frontend pipeline page (`/pipelines`)
- [ ] Write tests

---

## 12. Phase 8: Frontend Integration

### 12.1 New Pages

| Page | Route | Description |
|---|---|---|
| Workspaces | `/workspaces` | List, launch, stop, delete workspaces |
| Workspace Detail | `/workspaces/[id]` | Jupyter iframe, status, resource usage |
| Visualizations | `/visualizations` | Grid of visualizations with filters |
| Visualization Editor | `/visualizations/[id]` | Monaco editor + live preview |
| Dashboards | `/dashboards` | Grid of dashboard cards |
| Dashboard Editor | `/dashboards/[id]` | Drag-drop grid layout editor |
| Jobs | `/jobs` | List training/inference jobs |
| Job Detail | `/jobs/[id]` | Metrics chart, logs, progress |
| Experiments | `/experiments` | List experiments |
| Experiment Detail | `/experiments/[id]` | Run comparison (parallel coordinates) |
| Features | `/features` | Feature store browser |
| Pipelines | `/pipelines` | Pipeline list and run history |

### 12.2 Updated Sidebar

```
── Main ──
  Home (dashboard)
  Models
  Anomalies
  Cases
  Rules
  Alerts
  Entities
  Data Sources

── Develop ── (NEW)
  Workspaces
  Visualizations
  Dashboards
  Experiments
  Features
  Pipelines

── Monitor ── (NEW)
  Jobs
  Schedules

── Admin ──
  Users
  Settings
```

### 12.3 New Frontend Dependencies

```json
{
  "react-grid-layout": "^2.2.2",   // Dashboard drag-drop
  "@monaco-editor/react": "^4.7.0"  // Code editor (already available)
}
```

### 12.4 Implementation Checklist

- [ ] Create workspace list page
- [ ] Create workspace detail page (Jupyter iframe)
- [ ] Create visualization list page
- [ ] Create visualization editor page
- [ ] Port VizRenderer component
- [ ] Create dashboard list page
- [ ] Create dashboard editor page
- [ ] Create jobs list page
- [ ] Create job detail page (metrics chart + logs)
- [ ] Create experiments list page
- [ ] Create experiment comparison page
- [ ] Create features page
- [ ] Create pipelines page
- [ ] Update sidebar navigation
- [ ] Add workspace launcher dialog
- [ ] Add SSE client for metrics streaming
- [ ] Write frontend component tests

---

## 13. Kubernetes CRD Strategy

### 13.1 CRD Inventory

OpenUBA takes a CRD-native approach. Every orchestrated resource is a Custom Resource:

| CRD | Kind | Existing? | What It Manages |
|---|---|---|---|
| `ubatrainings.openuba.org` | UBATraining | **Yes** | Model training K8s Jobs |
| `ubainferences.openuba.org` | UBAInference | **Yes** | Model inference K8s Jobs |
| `ubaworkspaces.openuba.org` | UBAWorkspace | **New** | Jupyter workspace Pods + Services + PVCs |
| `ubajobs.openuba.org` | UBAJob | **New** | Generic job abstraction (supersedes direct Job creation) |
| `ubapipelines.openuba.org` | UBAPipeline | **New** | Multi-step pipeline orchestration |

### 13.2 Why CRDs Over Direct K8s API

OMS uses direct K8s API calls (kube-rs `Api<Job>::create()`). OpenUBA uses CRDs because:

1. **Declarative**: Describe desired state, operator reconciles
2. **Auditable**: `kubectl get ubaws` shows all workspaces
3. **Recoverable**: Operator can reconcile after crashes
4. **Observable**: `kubectl describe ubaws my-workspace` shows full status
5. **Extensible**: Webhooks, admission controllers, monitoring
6. **GitOps-Compatible**: CRs can be version-controlled

### 13.3 Operator Enhancements

**File:** `core/operator/main.py`

Add handlers for new CRDs:

```python
# Existing
@kopf.on.create('ubatrainings')
@kopf.on.create('ubainferences')

# New
@kopf.on.create('ubaworkspaces')
@kopf.on.delete('ubaworkspaces')
@kopf.on.timer('ubaworkspaces', interval=60)  # Health check + timeout

@kopf.on.create('ubapipelines')
@kopf.on.update('ubapipelines')
```

### 13.4 Implementation Checklist

- [ ] Create UBAWorkspace CRD YAML
- [ ] Create UBAPipeline CRD YAML
- [ ] Update existing UBATraining CRD with new fields
- [ ] Update existing UBAInference CRD with new fields
- [ ] Implement operator handlers for UBAWorkspace
- [ ] Implement operator handlers for UBAPipeline
- [ ] Update operator RBAC (create/read/delete Pods, Services, PVCs)
- [ ] Update operator Dockerfile
- [ ] Write operator integration tests
- [ ] Add `kubectl` printer columns for all CRDs

---

## 14. Database Schema Additions

### 14.1 New Tables Summary

| Table | Phase | Purpose |
|---|---|---|
| `workspaces` | 1 | Workspace metadata and status |
| `environments` | 1 | Custom workspace Docker images |
| `jobs` | 3 | Training/inference job records |
| `job_logs` | 3 | Per-job log entries |
| `training_metrics` | 3 | Per-job metric history |
| `visualizations` | 4 | Visualization records |
| `dashboards` | 5 | Dashboard records |
| `feature_groups` | 6 | Feature group metadata |
| `features` | 6 | Individual features with transforms |
| `experiments` | 6 | Experiment records |
| `experiment_runs` | 6 | Per-experiment run records |
| `hyperparameter_sets` | 6 | Stored hyperparameter configurations |
| `pipelines` | 7 | Pipeline definitions |
| `pipeline_runs` | 7 | Pipeline execution records |
| `datasets` | 2 | Dataset metadata (enhanced from existing) |
| `model_versions` | 2 | Model version history |

### 14.2 Migration Strategy

Use Alembic (already in requirements.txt) for schema migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "add workspaces table"

# Apply migration
alembic upgrade head
```

Each phase gets its own migration file to keep changes traceable.

### 14.3 Implementation Checklist

- [ ] Create migration: Phase 1 (workspaces, environments)
- [ ] Create migration: Phase 2 (datasets enhanced, model_versions)
- [ ] Create migration: Phase 3 (jobs, job_logs, training_metrics)
- [ ] Create migration: Phase 4 (visualizations)
- [ ] Create migration: Phase 5 (dashboards)
- [ ] Create migration: Phase 6 (feature_groups, features, experiments, experiment_runs, hyperparameter_sets)
- [ ] Create migration: Phase 7 (pipelines, pipeline_runs)
- [ ] Test forward and rollback migrations
- [ ] Update `core/db/schema.sql` with full schema
- [ ] Update `core/db/init_schema.py`

---

## 15. API Endpoint Design

### 15.1 New Endpoint Summary

| Method | Path | Phase | Description |
|---|---|---|---|
| POST | `/api/v1/workspaces/launch` | 1 | Launch workspace |
| GET | `/api/v1/workspaces` | 1 | List workspaces |
| GET | `/api/v1/workspaces/{id}` | 1 | Get workspace |
| DELETE | `/api/v1/workspaces/{id}` | 1 | Delete workspace |
| POST | `/api/v1/workspaces/{id}/stop` | 1 | Stop workspace |
| POST | `/api/v1/workspaces/{id}/restart` | 1 | Restart workspace |
| POST | `/api/v1/sdk/register-model` | 2 | Register model from SDK |
| POST | `/api/v1/sdk/publish-version` | 2 | Publish model version |
| GET | `/api/v1/sdk/models/resolve/{name}` | 2 | Resolve model by name |
| POST | `/api/v1/sdk/create-dataset` | 2 | Create dataset from SDK |
| GET | `/api/v1/sdk/datasets` | 2 | List datasets |
| GET | `/api/v1/sdk/datasets/{id}/content` | 2 | Download dataset |
| POST | `/api/v1/sdk/start-training` | 3 | Start training job |
| POST | `/api/v1/sdk/start-inference` | 3 | Start inference job |
| GET | `/api/v1/jobs` | 3 | List jobs |
| GET | `/api/v1/jobs/{id}` | 3 | Get job details |
| GET | `/api/v1/jobs/{id}/metrics/stream` | 3 | SSE metrics stream |
| POST | `/api/v1/internal/metrics/{job_id}` | 3 | Post metrics (internal) |
| POST | `/api/v1/internal/logs/{job_id}` | 3 | Post logs (internal) |
| GET | `/api/v1/jobs/{id}/logs` | 3 | Get job logs |
| POST | `/api/v1/visualizations` | 4 | Create visualization |
| GET | `/api/v1/visualizations` | 4 | List visualizations |
| GET | `/api/v1/visualizations/{id}` | 4 | Get visualization |
| PUT | `/api/v1/visualizations/{id}` | 4 | Update visualization |
| DELETE | `/api/v1/visualizations/{id}` | 4 | Delete visualization |
| POST | `/api/v1/visualizations/{id}/publish` | 4 | Publish visualization |
| POST | `/api/v1/dashboards` | 5 | Create dashboard |
| GET | `/api/v1/dashboards` | 5 | List dashboards |
| GET | `/api/v1/dashboards/{id}` | 5 | Get dashboard |
| PUT | `/api/v1/dashboards/{id}` | 5 | Update dashboard |
| DELETE | `/api/v1/dashboards/{id}` | 5 | Delete dashboard |
| POST | `/api/v1/features` | 6 | Create features |
| GET | `/api/v1/features/group/{name}` | 6 | Load feature group |
| POST | `/api/v1/experiments` | 6 | Create experiment |
| GET | `/api/v1/experiments` | 6 | List experiments |
| GET | `/api/v1/experiments/{id}` | 6 | Get experiment |
| POST | `/api/v1/experiments/{id}/runs` | 6 | Add experiment run |
| GET | `/api/v1/experiments/{id}/compare` | 6 | Compare runs |
| POST | `/api/v1/hyperparameters` | 6 | Create hyperparameter set |
| GET | `/api/v1/hyperparameters` | 6 | List hyperparameter sets |
| POST | `/api/v1/pipelines` | 7 | Create pipeline |
| GET | `/api/v1/pipelines` | 7 | List pipelines |
| POST | `/api/v1/pipelines/{id}/run` | 7 | Run pipeline |
| GET | `/api/v1/pipelines/{id}/status` | 7 | Get pipeline status |

### 15.2 SDK vs. API Endpoints

SDK endpoints (`/api/v1/sdk/*`) are designed for notebook/programmatic use:
- Simplified request/response formats
- Auto-resolve by name or ID
- Accept inline data (base64-encoded)
- Return minimal responses

API endpoints (`/api/v1/*`) are designed for UI consumption:
- Full CRUD with pagination
- Rich response with relationships
- Filter/sort parameters
- Streaming endpoints (SSE)

---

## 16. Security Considerations

### 16.1 Workspace Security

- **Workspace JWT tokens** have 30-day expiry and are scoped to a specific workspace
- **Pod network policy**: Workspace pods can only reach the backend API and data sources (not other workspaces)
- **PVC isolation**: Each workspace has its own PVC, no cross-workspace access
- **Resource limits**: Hardware tiers enforce CPU/memory/GPU limits
- **Timeout**: Workspaces auto-stop after configurable timeout (default: 24h)
- **Non-root execution**: Workspace containers run as `jovyan` user (uid 1000)

### 16.2 Model Execution Security

- **Existing**: SHA-256 hash verification for installed models
- **New**: SDK-registered models run in isolated K8s Jobs
- **Resource limits**: Hardware tiers enforce resource boundaries
- **No persistent access**: Job pods are ephemeral, destroyed after completion
- **Internal-only endpoints**: `/api/v1/internal/*` endpoints are only accessible from within the K8s cluster

### 16.3 RBAC Integration

New permissions for existing roles:

| Permission | admin | manager | analyst | triage |
|---|---|---|---|---|
| workspaces (r/w) | rw | r | rw | - |
| visualizations (r/w) | rw | r | rw | r |
| dashboards (r/w) | rw | r | rw | r |
| experiments (r/w) | rw | r | rw | - |
| features (r/w) | rw | r | rw | - |
| jobs (r/w) | rw | r | rw | - |
| pipelines (r/w) | rw | r | rw | - |

---

## 17. Testing Strategy

### 17.1 Unit Tests

- SDK client methods (mock HTTP)
- Visualization renderers (mock backends)
- API router handlers (TestClient)
- Database repository methods (test DB)
- CRD validation

### 17.2 Integration Tests

- Workspace launch → access → stop → delete
- Model register → train → infer lifecycle
- Visualization create → render → publish → dashboard
- Pipeline create → run → complete
- Feature store create → load → transform

### 17.3 E2E Tests

- Full notebook workflow in workspace
- Dashboard creation from UI
- Job monitoring with metrics streaming
- Experiment comparison workflow

### 17.4 Test Files

```
core/tests/
├── test_api_routers/
│   ├── test_workspaces.py      (new)
│   ├── test_visualizations.py  (new)
│   ├── test_dashboards.py      (new)
│   ├── test_jobs.py            (new)
│   ├── test_experiments.py     (new)
│   ├── test_features.py        (new)
│   ├── test_pipelines.py       (new)
│   └── test_sdk_endpoints.py   (new)
├── test_services/
│   ├── test_workspace_service.py  (new)
│   └── test_job_service.py        (new)
├── e2e/
│   ├── test_workspace_lifecycle.py  (new)
│   └── test_full_ml_workflow.py     (new)
sdk/tests/
├── test_client.py              (new)
├── test_visualization.py       (new)
├── test_registry.py            (enhanced)
└── test_context.py             (new)
```

---

## 18. Migration & Compatibility

### 18.1 Backward Compatibility

All changes are additive:
- Existing models in `/core/model_library/` continue to work unchanged
- Existing API endpoints remain unchanged
- Existing CRDs (UBATraining, UBAInference) remain backward-compatible (new fields are optional)
- Existing frontend pages remain unchanged
- Existing SDK commands (install, run, list) remain unchanged

### 18.2 Migration Path

1. **Database**: Run Alembic migrations (no data loss, only additive)
2. **K8s**: Apply new CRDs, update operator deployment
3. **Docker**: Build new workspace image, update runner images
4. **Frontend**: Deploy new pages (existing pages untouched)
5. **SDK**: Pip install updated `openuba` package

### 18.3 Feature Flags

For gradual rollout, features can be gated:

```python
# core/config.py
ENABLE_WORKSPACES = os.getenv("ENABLE_WORKSPACES", "true").lower() == "true"
ENABLE_VISUALIZATIONS = os.getenv("ENABLE_VISUALIZATIONS", "true").lower() == "true"
ENABLE_DASHBOARDS = os.getenv("ENABLE_DASHBOARDS", "true").lower() == "true"
ENABLE_EXPERIMENTS = os.getenv("ENABLE_EXPERIMENTS", "true").lower() == "true"
ENABLE_PIPELINES = os.getenv("ENABLE_PIPELINES", "true").lower() == "true"
```

---

## 19. OMS Feature Graduation Pipeline

### 19.1 Process

```
1. Feature is developed and stabilized in OMS
2. Feature is added to OpenUBA roadmap
3. Feature is adapted for UBA domain:
   - Security-specific templates/presets
   - Integration with anomaly/case/rule systems
   - CRD-native K8s orchestration
   - RBAC-aware access control
4. Feature is implemented in OpenUBA
5. Feature is tested end-to-end
6. Feature is released
```

### 19.2 OMS Features Ready for Graduation

| OMS Feature | Status in OMS | Priority for OpenUBA | Notes |
|---|---|---|---|
| Workspaces | Stable | **P0 — Critical** | Foundation for all other features |
| Python SDK | Stable | **P0 — Critical** | Enables notebook workflow |
| Visualization (9 backends) | Stable | **P1 — High** | Security data viz |
| Dashboard framework | Stable | **P1 — High** | SOC dashboards |
| Jobs system | Stable | **P1 — High** | Enhanced training/inference |
| Feature store | Stable | **P2 — Medium** | Feature engineering |
| Experiment tracking | Stable | **P2 — Medium** | Hyperparameter comparison |
| Hyperparameter store | Stable | **P2 — Medium** | Parameter management |
| Pipelines | Stable | **P2 — Medium** | Workflow automation |
| Hyperparameter sweeps | Stable | **P3 — Low** | AutoML-lite |
| Model versioning | Stable | **P3 — Low** | Version history |
| LLM tools (agentic) | Stable | **P3 — Low** | AI assistant tool use |
| Environment management | Stable | **P3 — Low** | Custom workspace images |
| Notifications | Stable | **P3 — Low** | In-app notifications |

### 19.3 Future OMS Features to Watch

Features being developed in OMS that may graduate later:
- AutoML (hyperparameter search UI)
- Model serving endpoints
- Data source connectors (Kafka, SQL databases)
- Collaborative editing
- Template marketplace

---

## 20. Implementation Checklist

### Phase 1: Workspace System (Foundation)
- [ ] Create UBAWorkspace CRD YAML (`k8s/crds/ubaworkspace-crd.yaml`)
- [ ] Implement Kopf operator handler (`core/operator/workspace_handler.py`)
- [ ] Build workspace Docker image (`docker/workspace/Dockerfile`)
- [ ] Create workspace database model + Alembic migration
- [ ] Create workspace repository (`core/repositories/workspace_repository.py`)
- [ ] Create workspace service (`core/services/workspace_service.py`)
- [ ] Create workspace API router (`core/api_routers/workspaces.py`)
- [ ] Create workspace Pydantic schemas (`core/api_schemas/workspaces.py`)
- [ ] Add workspace JWT token generation
- [ ] Implement NodePort allocation logic
- [ ] Create welcome.ipynb notebook (`workspace/welcome.ipynb`)
- [ ] Create workspace list frontend page
- [ ] Create workspace detail frontend page (Jupyter iframe)
- [ ] Add workspace to sidebar navigation
- [ ] Add Makefile targets (`build-workspace`, `deploy-workspace`)
- [ ] Update operator RBAC
- [ ] Write unit tests
- [ ] Write integration tests

### Phase 2: Enhanced `openuba` Python Package
- [ ] Redesign `sdk/src/openuba/client.py` with full API client
- [ ] Add `sdk/src/openuba/visualization.py` (9 backends)
- [ ] Add `sdk/src/openuba/context.py` (ModelContext)
- [ ] Enhance model.py with singleton convenience functions
- [ ] Enhance registry.py with platform API integration
- [ ] Enhance config.py with project root detection
- [ ] Enhance cli.py with new commands
- [ ] Update __init__.py with all exports
- [ ] Add framework auto-detection
- [ ] Add model serialization
- [ ] Add source code generation
- [ ] Add UBA-specific query methods
- [ ] Add SDK endpoints to backend API
- [ ] Create dataset management API
- [ ] Update pyproject.toml
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create example notebooks

### Phase 3: Jobs & Execution Engine
- [ ] Create Job database model + migration
- [ ] Create JobLog database model
- [ ] Create TrainingMetric database model
- [ ] Create job API router
- [ ] Create internal metrics endpoint
- [ ] Create internal logs endpoint
- [ ] Implement SSE metrics streaming
- [ ] Enhance UBATraining CRD with new fields
- [ ] Enhance UBAInference CRD with new fields
- [ ] Update Kopf operator handlers
- [ ] Enhance model runner with MetricReporter
- [ ] Enhance model runner with ModelLogHandler
- [ ] Enhance model runner with ModelContext
- [ ] Create jobs list frontend page
- [ ] Create job detail frontend page
- [ ] Implement frontend SSE client for metrics
- [ ] Write tests

### Phase 4: Visualization Framework
- [ ] Create Visualization database model + migration
- [ ] Create visualization API router
- [ ] Port VizRenderer to frontend
- [ ] Create visualization list page
- [ ] Create visualization editor page
- [ ] Integrate Monaco editor for code editing
- [ ] Create backend template code (9 backends)
- [ ] Create UBA-specific visualization templates (10 templates)
- [ ] Add to sidebar
- [ ] Write tests

### Phase 5: Dashboard Framework
- [ ] Create Dashboard database model + migration
- [ ] Create dashboard API router
- [ ] Add react-grid-layout dependency
- [ ] Create dashboard list page
- [ ] Create dashboard editor page
- [ ] Implement LazyVizPanel (IntersectionObserver)
- [ ] Implement drag-drop, resize, lock/unlock
- [ ] Implement responsive breakpoints
- [ ] Create pre-built dashboard templates
- [ ] Add to sidebar
- [ ] Write tests

### Phase 6: Feature Store & Experiment Tracking
- [ ] Create FeatureGroup + Feature database models + migration
- [ ] Create Experiment + ExperimentRun database models + migration
- [ ] Create HyperparameterSet database model + migration
- [ ] Create feature store API router
- [ ] Create experiments API router
- [ ] Create hyperparameters API router
- [ ] Add SDK methods
- [ ] Create frontend pages
- [ ] Add experiment comparison view
- [ ] Write tests

### Phase 7: Pipeline System
- [ ] Create UBAPipeline CRD
- [ ] Implement Kopf operator handler
- [ ] Create Pipeline + PipelineRun database models + migration
- [ ] Create pipeline API router
- [ ] Add SDK methods
- [ ] Create frontend page
- [ ] Write tests

### Phase 8: Frontend Integration
- [ ] Update sidebar with new sections (Develop, Monitor)
- [ ] Ensure all new pages have consistent design
- [ ] Add workspace launcher to command palette
- [ ] Add keyboard shortcuts for common actions
- [ ] Update home dashboard with new widgets
- [ ] Add project scoping to all new pages
- [ ] Performance audit (lazy loading, code splitting)
- [ ] Accessibility audit
- [ ] Write frontend component tests

### Cross-Cutting
- [ ] Update `requirements.txt` with new dependencies
- [ ] Update `docker-compose.yaml` with workspace service
- [ ] Update `Makefile` with new targets
- [ ] Update RBAC permissions for new features
- [ ] Update `core/fastapi_app.py` to include new routers
- [ ] Create database seed data for new features
- [ ] Update CI/CD pipeline for new Docker images
- [ ] Update README.md with new features
- [ ] Create user documentation for each new feature
- [ ] Performance testing under load
- [ ] Security review

---

## Appendix A: Key File Paths (Reference)

### OpenUBA (Current)
| Path | Purpose |
|---|---|
| `core/fastapi_app.py` | FastAPI app entry |
| `core/operator/main.py` | Kopf K8s operator |
| `core/services/model_orchestrator.py` | Model execution |
| `core/services/model_installer.py` | Model installation |
| `core/services/rule_engine.py` | Rule evaluation |
| `core/db/models.py` | SQLAlchemy models |
| `core/db/schema.sql` | DB schema |
| `core/auth.py` | JWT + RBAC |
| `core/api_routers/` | 14 API router modules |
| `sdk/src/openuba/` | Python SDK |
| `docker/model-runner/runner.py` | Model runner |
| `k8s/crds/` | UBATraining + UBAInference CRDs |
| `interface/src/` | Next.js frontend |

### OpenModelStudio (Reference)
| Path | Purpose |
|---|---|
| `api/src/services/k8s.rs` | K8s pod/job management |
| `api/src/routes/workspaces.rs` | Workspace endpoints |
| `api/src/routes/visualizations.rs` | Visualization endpoints |
| `api/src/routes/training.rs` | Training job endpoints |
| `sdk/python/openmodelstudio/client.py` | Python SDK (1658 lines) |
| `sdk/python/openmodelstudio/visualization.py` | Viz framework (474 lines) |
| `model-runner/python/runner.py` | Model runner |
| `model-runner/python/context.py` | ModelContext |
| `web/src/components/shared/viz-renderer.tsx` | VizRenderer |
| `web/src/app/dashboards/[id]/page.tsx` | Dashboard editor |
| `db/init.sql` | Full schema (27 tables) |

---

## Appendix B: Environment Variables (New)

| Variable | Purpose | Default |
|---|---|---|
| `OPENUBA_WORKSPACE_ID` | Current workspace UUID (set in pods) | — |
| `OPENUBA_PROJECT_ID` | Current project UUID (set in pods) | — |
| `ENABLE_WORKSPACES` | Feature flag | `true` |
| `ENABLE_VISUALIZATIONS` | Feature flag | `true` |
| `ENABLE_DASHBOARDS` | Feature flag | `true` |
| `ENABLE_EXPERIMENTS` | Feature flag | `true` |
| `ENABLE_PIPELINES` | Feature flag | `true` |
| `WORKSPACE_NODE_PORT_START` | NodePort range start | `31100` |
| `WORKSPACE_NODE_PORT_END` | NodePort range end | `31199` |
| `WORKSPACE_DEFAULT_TIMEOUT` | Default timeout hours | `24` |
| `WORKSPACE_DEFAULT_PVC_SIZE` | Default PVC size | `5Gi` |
| `METRICS_FLUSH_INTERVAL` | Metrics batch interval (seconds) | `2` |
| `LOG_FLUSH_INTERVAL` | Log batch interval (seconds) | `2` |

---

## Appendix C: Docker Image Inventory (Updated)

| Image | Existing? | Purpose |
|---|---|---|
| `openuba-backend:latest` | Yes | FastAPI backend |
| `openuba-frontend:latest` | Yes | Next.js frontend |
| `openuba-operator:latest` | Yes | Kopf K8s operator |
| `openuba-model-runner:base` | Yes | Base runner + PySpark |
| `openuba-model-runner:sklearn` | Yes | + scikit-learn |
| `openuba-model-runner:pytorch` | Yes | + PyTorch |
| `openuba-model-runner:tensorflow` | Yes | + TensorFlow |
| `openuba-model-runner:networkx` | Yes | + NetworkX |
| `openuba-workspace:latest` | **New** | Jupyter + openuba SDK + all viz libs |

---

## Appendix D: Makefile Targets (New)

```makefile
# Workspace
build-workspace:
	docker build -f docker/workspace/Dockerfile -t openuba-workspace:latest .

# Full build (updated)
build-containers: build-backend build-frontend build-model-runner build-operator build-workspace

# CRDs
apply-crds:
	kubectl apply -f k8s/crds/

# Development
dev-workspace:
	@echo "Launch workspace: POST http://localhost:8000/api/v1/workspaces/launch"
```

---

*This document is a living plan. Update as implementation progresses.*
*Last updated: 2026-03-14*
