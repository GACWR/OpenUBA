# OpenUBA Roadmap

## Vision

OpenUBA aims to be the standard open-source User & Entity Behavior Analytics (UEBA) platform for cloud-native security operations.

## Current State (v0.0.2)

### Core Engine
- FastAPI backend with REST API (24 routers under `core/api_routers/`)
- Containerized model execution sandbox (Docker-based, `docker/model-runner/runner.py`)
- Dual data pipelines: Elasticsearch + Apache Spark
- 5 ML runtime images: sklearn, pytorch, tensorflow, networkx, base
- Next.js frontend with model management UI (`interface/`, Next.js 14)
- PostgreSQL storage (single-instance Deployment in `k8s/postgres.yaml`)
- Local model library with install/train/infer lifecycle (10+ reference models in `core/model_library/`)
- Kind cluster development environment (`configs/local.yaml`, `make` targets)

### Kubernetes-Native Infrastructure
- Custom Resource Definitions: UBATraining, UBAInference, UBAPipeline, UBAWorkspace (group `openuba.io`)
- Kopf-based operator (`core/operator/`) with workspace, training, inference, and pipeline handlers
- Operator deployment, RBAC, and service accounts (`k8s/operator-deployment.yaml`, `k8s/operator-rbac.yaml`)
- Full K8s manifest set (19 yaml files): backend, frontend, Elasticsearch, Spark, Postgres, PostGraphile, operator, ingress, namespace, PV/PVCs, secrets

### Model Registry & Ecosystem
- Multi-backend model registry with adapter pattern (`core/registry/registry_service.py`)
- Adapters for code registries (local FS, GitHub, OpenUBA Hub) and weights registries (local FS, HuggingFace, Kubeflow)
- Registry service with unit tests (`core/tests/test_registry/`)
- Install-time SHA-256 model integrity verification (`core/services/model_installer.py`) that gates installation on a checksum match
- **Community model marketplace — OpenUBA Hub LIVE at https://openuba.org** (Next.js Model Hub in sibling repo `openuba-model-hub`, CNAME `openuba.org`, static catalog of reference models). Backend client adapter ships in `core/registry/adapters/openuba_hub_adapter.py`.

### Scheduling & Async
- Model scheduler service (`core/services/model_scheduler.py`, APScheduler or K8s CronJob mode)
- Schedules API router (`core/api_routers/schedules.py`)
- Async inference and training endpoints; operator dispatches `UBAInference` / `UBATraining` CRs

### GraphQL
- PostGraphile deployment (`k8s/postgraphile-deployment.yaml`) plus dev-mode local PostGraphile bootstrap (`core/graphql/postgraphile.py`)
- GraphQL endpoint exposed (smoke test only at `core/tests/test_graphql.py` — does not exercise a real query; query coverage planned in Phase 1)

### Workspaces
- Jupyter notebook workspaces with hardware tiers and NodePort allocation (`core/services/workspace_service.py`)
- Workspace CRD + Kopf operator handler (`core/operator/workspace_handler.py`)
- Python SDK installable as `openuba` v0.0.2 (`sdk/src/openuba/`)

### Testing
- Comprehensive E2E test suite: 24 flow tests, 5,636 LOC across `core/tests/e2e/` covering anomalies, cases, dashboards, datasets, display, experiments, features, jobs, model lifecycle, pipelines, navigation, rules, visualizations, workspaces, and JupyterLab SDK

### Visual Rule Builder (Rule Canvas)
- ReactFlow-based drag-and-drop rule editor (664 LOC, `flow-canvas.tsx`)
- Custom node types for detection logic (290 LOC, `flow-nodes.tsx`)
- Palette with draggable condition/action nodes
- Rule save, test, severity configuration
- Integrated with GraphQL model queries

### LLM Investigation Assistant
- Omnipresent chat window accessible from any page (559 LOC, `chat-window.tsx`)
- Multi-provider support: Ollama, OpenAI, Claude, Gemini (538-LOC `chat_service.py` with per-provider streaming)
- SSE streaming with thinking-block parsing
- Context-aware: injects current page/entity context into prompts
- Backend chat API with SSE streaming (`interface/app/api/chat/route.ts` proxying to `core/api_routers/chat.py`)

### Governance Framework
- CNCF-shaped governance files shipped: `GOVERNANCE.md`, `MAINTAINERS.md`, `CONTRIBUTING.md` (DCO required), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SECURITY.md`, `ADOPTERS.md` (PR #137). Substantive, non-boilerplate — see Phase 4 note on demonstrating use of the framework.

## Known Gaps in Current State

Honest list of items the Current State touches but does not fully deliver, with code citations:

- `/metrics` endpoint at `core/api_routers/data.py:201` emits domain JSON (Spark/ES counters), not Prometheus exposition format. No `opentelemetry-*` or `prometheus_client` in `requirements.txt`; no OpenTelemetry SDK init in `core/`.
- `core/tests/test_graphql.py` is a 24-LOC smoke test (GETs `/`, checks for an `endpoints` key) — does not exercise a GraphQL query, schema introspection, or PostGraphile.
- `core/registry/adapters/openuba_hub_adapter.py` now defaults to `https://openuba.org`, but the live Hub serves a static Next.js catalog rather than the `/ml/` JSON contract the adapter expects — Hub-side JSON endpoint needs publishing.
- `k8s/postgres.yaml` is a vanilla single-replica Deployment + PVC, not CloudNativePG. HA Postgres moved to Phase 1.

## Phase 1: Production Hardening (Q3 2026)

- [ ] Helm chart packaging and publishing to Artifact Hub (`k8s/` is raw manifests today; no `Chart.yaml`, no `helm/` directory, no `helm` Makefile target)
- [ ] Horizontal pod autoscaling for Spark workers (`k8s/spark-deployment.yaml` hardcodes `replicas: 1`; no `autoscaling/v2` resources anywhere)
- [ ] Multi-tenant isolation (namespace-per-tenant + `tenant_id` across tables / repositories / RBAC; today there is one `openuba` namespace and zero tenant-scoped code)
- [ ] Production-grade observability — Prometheus exposition-format `/metrics` + OpenTelemetry SDK self-instrumentation (current: domain-JSON metrics endpoint only)
- [ ] Migrate Postgres deployment to CloudNativePG operator (HA `Cluster` CR, automated failover, scheduled backups) — moved here from Current State per audit
- [ ] GraphQL query-level test coverage (replace smoke test with real query / mutation / schema-introspection suite against PostGraphile)

## Phase 2: CNCF Integration (Q4 2026)

- [ ] Falco integration — consume runtime security events as behavioral data source (no Falco consumer code today; aspirational mentions only)
- [ ] OpenTelemetry ingest — receive OTLP traces and logs as behavioral signals (distinct from Phase 1 emit; no OTLP receiver or collector config in repo)
- [ ] OPA / Kyverno policy trigger — output risk scores in OPA-input JSON shape with example `ClusterPolicy` wiring
- [ ] SPIFFE / SPIRE workload identity for inter-service authentication (current inter-service auth is JWT/bearer via `python-jose`)
- [ ] CNCF Landscape listing (PR to `cncf/landscape` under Security & Compliance)
- [ ] TAG Security presentation and feedback incorporation

## Phase 3: Community & Scale (Q1 2027)

- [ ] Performance benchmarks published (no `bench/`, `benchmarks/`, or `docs/performance/` today; README has no numeric throughput / latency / scale claims)
- [ ] Contributor diversity (multiple organizations) — **the longest pole**; see governance note in Phase 4. 12-month commit history shows one human author + dependabot; `MAINTAINERS.md` lists 1 maintainer.

*(The "Community model marketplace (OpenUBA Hub public instance)" item previously listed here has moved to Current State — the Hub is live at https://openuba.org. The remaining adapter-URL fix is tracked in Known Gaps.)*

## Phase 4: Incubation Readiness (Q2 2027)

- [ ] Production deployments documented in `ADOPTERS.md` — recruit 3+ independent adopters (file exists with 1 entry: the project's host org)
- [ ] Independent security audit (engage e.g. OSTIF / Trail of Bits / CNCF-sponsored; publish report in `docs/audit/`)
- [ ] Comprehensive documentation review — docs site (no `mkdocs.yml` / Docusaurus / Sphinx today), API reference, operator runbook, tutorial series; reconcile Python version drift between `docs/ARCHITECTURE.md` (3.9) and `CONTRIBUTING.md` (3.11+)
- [ ] Governance maturity demonstration — see note below

### Note on governance maturity (longest pole)

The governance framework is **shipped** — `GOVERNANCE.md`, `MAINTAINERS.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ADOPTERS.md` (PR #137). What is missing is *demonstration of using it*: the 2-maintainer approval path defined in `GOVERNANCE.md` is currently inoperable with 1 maintainer, `ADOPTERS.md` has 1 entry (the host org), there are no public TSC meeting notes, and no governance-tagged decisions on record. Both blockers resolve only via sustained external contributor + adopter outreach — i.e., they bottleneck on Phase 3's contributor-diversity item, which is the steepest CNCF Sandbox → Incubation gate this project faces.

