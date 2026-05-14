# OpenUBA Roadmap

## Vision

OpenUBA aims to be the standard open-source User & Entity Behavior Analytics (UEBA) platform for cloud-native security operations.

## Current State (v0.0.2)

- FastAPI backend with REST API
- Containerized model execution sandbox (Docker-based)
- Dual data pipelines: Elasticsearch + Apache Spark
- 5 ML runtime images: sklearn, pytorch, tensorflow, networkx, base
- Next.js frontend with model management UI
- PostgreSQL storage with CloudNativePG
- Local model library with install/train/infer lifecycle
- Kind cluster development environment

## Phase 1: Production Hardening (Q3 2026)

- [ ] Kubernetes-native CRDs: `UBAModel`, `UBATraining`, `UBAInference`
- [ ] OpenUBA Operator for K8s Job orchestration
- [ ] `KubernetesJobExecutionDriver` (production replacement for `LocalDockerExecutionDriver`)
- [ ] Model integrity verification (hash checks on install + pre-execution)
- [ ] Async inference API (POST returns job_id, GET to poll)
- [ ] Scheduled inference via CronJobs
- [ ] Full PostgreSQL data model migration (replace JSON file state)

## Phase 2: Ecosystem & Integration (Q4 2026)

- [ ] Multi-backend model registry (GitHub adapter, HuggingFace adapter, OpenUBA Hub)
- [ ] Falco integration: consume runtime security events as behavioral data source
- [ ] OpenTelemetry integration: ingest OTLP traces and logs
- [ ] Prometheus metrics exporter (`/metrics` endpoint)
- [ ] OPA/Kyverno policy trigger: output risk scores as policy inputs
- [ ] GraphQL API via PostGraphile
- [ ] Helm chart publishing to Artifact Hub

## Phase 3: Scale & Community (Q1 2027)

- [ ] Horizontal scaling for Spark workers
- [ ] Multi-tenant support
- [ ] Visual Rule Builder for non-ML detection logic
- [ ] LLM-powered investigation assistant
- [ ] Community model marketplace (OpenUBA Hub)
- [ ] CNCF Landscape listing
- [ ] TAG Security presentation and feedback incorporation

## Phase 4: Incubation Readiness (Q2 2027)

- [ ] Production deployments documented in ADOPTERS.md
- [ ] Independent security audit
- [ ] Contributor diversity (multiple organizations)
- [ ] Comprehensive observability (OpenTelemetry self-instrumentation)
- [ ] Performance benchmarks published
