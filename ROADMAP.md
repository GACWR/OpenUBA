# OpenUBA Roadmap

## Vision

OpenUBA aims to be the standard open-source User & Entity Behavior Analytics (UEBA) platform for cloud-native security operations.

## Current State (v0.0.2)

### Core Engine
- FastAPI backend with REST API
- Containerized model execution sandbox (Docker-based)
- Dual data pipelines: Elasticsearch + Apache Spark
- 5 ML runtime images: sklearn, pytorch, tensorflow, networkx, base
- Next.js frontend with model management UI
- PostgreSQL storage with CloudNativePG
- Local model library with install/train/infer lifecycle
- Kind cluster development environment

### Kubernetes-Native Infrastructure
- Custom Resource Definitions: UBATraining, UBAInference, UBAPipeline, UBAWorkspace
- Kopf-based operator (core/operator/) with workspace and pipeline handlers
- Operator deployment, RBAC, and service accounts (k8s/)
- Full K8s manifests: backend, frontend, Elasticsearch, Spark, Postgres, ingress

### Model Registry & Ecosystem
- Multi-backend model registry with adapter pattern
- Adapters: local filesystem, GitHub, HuggingFace, Kubeflow, OpenUBA Hub
- Model integrity verification via SHA-256 hashing (core/hash.py)
- Registry service with tests

### Scheduling & Async
- Model scheduler service (core/services/model_scheduler.py)
- Schedules API router (core/api_routers/schedules.py)
- Async inference support in pipeline

### GraphQL
- PostGraphile deployment (k8s/postgraphile-deployment.yaml)
- GraphQL endpoint with tests (core/tests/test_graphql.py)

### Workspaces
- Jupyter notebook workspaces with SDK integration
- Workspace CRD + operator handler
- E2E tests for workspace notebooks and JupyterLab SDK

### Visual Rule Builder (Rule Canvas)
- ReactFlow-based drag-and-drop rule editor (664 LOC, flow-canvas.tsx)
- Custom node types for detection logic (290 LOC, flow-nodes.tsx)
- Palette with draggable condition/action nodes
- Rule save, test, severity configuration
- Integrated with GraphQL model queries

### LLM Investigation Assistant
- Omnipresent chat window accessible from any page (559 LOC, chat-window.tsx)
- Multi-provider support: Ollama, OpenAI, Claude, Gemini
- SSE streaming with thinking block parsing
- Context-aware: injects current page/entity context into prompts
- Backend chat API with SSE streaming (app/api/chat/route.ts)

## Phase 1: Production Hardening (Q3 2026)

- [ ] Helm chart packaging and publishing to Artifact Hub
- [ ] Horizontal pod autoscaling for Spark workers
- [ ] Multi-tenant isolation (namespace-per-tenant)
- [ ] Production-grade observability (OpenTelemetry self-instrumentation, Prometheus /metrics endpoint)
- [ ] Full PostgreSQL migration for all state (eliminate remaining JSON file state)

## Phase 2: CNCF Integration (Q4 2026)

- [ ] Falco integration: consume runtime security events as behavioral data source
- [ ] OpenTelemetry integration: ingest OTLP traces and logs as behavioral signals
- [ ] OPA/Kyverno policy trigger: output risk scores as policy inputs
- [ ] SPIFFE/SPIRE workload identity for inter-service authentication
- [ ] CNCF Landscape listing
- [ ] TAG Security presentation and feedback incorporation

## Phase 3: Community & Scale (Q1 2027)

- [ ] Community model marketplace (OpenUBA Hub public instance)
- [ ] Performance benchmarks published
- [ ] Contributor diversity (multiple organizations)

## Phase 4: Incubation Readiness (Q2 2027)

- [ ] Production deployments documented in ADOPTERS.md
- [ ] Independent security audit
- [ ] Comprehensive documentation review
- [ ] Governance maturity demonstration
