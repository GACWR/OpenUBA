# Installation

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 20.10+ | Container builds and Kind cluster |
| Kind | 0.20+ | Local Kubernetes cluster |
| kubectl | 1.27+ | Kubernetes CLI |
| Python | 3.9+ | Backend and tests |
| Node.js | 18+ | Frontend build |
| pnpm or npm | latest | Frontend package manager |

## Quick Start

Clone the repository:

```bash
git clone https://github.com/GACWR/OpenUBA.git
cd OpenUBA
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
make dev-install-frontend
```

Start the full development environment:

```bash
make reset-dev
```

This single command:
1. Tears down any existing Kind cluster
2. Creates a new Kind cluster (`configs/local.yaml`)
3. Builds all Docker images (backend, frontend, operator, model runners)
4. Loads images into the Kind cluster
5. Deploys all Kubernetes resources (namespace, CRDs, operator, Postgres, Spark, Elasticsearch, PostGraphile, backend, frontend)
6. Opens terminal tabs for port forwarding, local backend, and local frontend

Once complete:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- GraphQL Playground: http://localhost:5001/graphiql
- Spark UI: http://localhost:8080

## Development Workflow

### Restarting after code changes

After modifying backend code:

```bash
make dev-restart-backend
```

After modifying frontend code:

```bash
make dev-restart-frontend
```

After modifying the operator:

```bash
make dev-restart-operator
```

Each command rebuilds the image, loads it into Kind, and triggers a rollout restart.

### Database

Initialize the database schema:

```bash
make init-db
```

For local (non-K8s) Postgres:

```bash
make init-db-local
```

Reset the database:

```bash
python scripts/reset_db.py
```

### Data Ingestion

Trigger ingestion of the included test dataset (`test_datasets/toy_1`) into Spark and Elasticsearch:

```bash
make k8s-init-data
```

This calls the backend API to ingest SSH, DNS, DHCP, and proxy log data.

## Running Tests

Unit and integration tests:

```bash
make test
```

Individual test suites:

```bash
make test-unit
make test-integration
make test-api
make test-repositories
make test-registry
make test-services
```

End-to-end tests (requires a running cluster):

```bash
make e2e-setup        # install Playwright and Chromium
make e2e-test         # run all E2E tests
```

E2E by page:

```bash
make e2e-test-models
make e2e-test-anomalies
make e2e-test-cases
make e2e-test-rules
make e2e-test-display
```

Full E2E pipeline (build, deploy, test, cleanup):

```bash
make e2e-full
```

Run everything:

```bash
make test-all
```

## Port Reference

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| PostGraphile (GraphQL) | 5001 |
| PostgreSQL | 5432 |
| Spark Master UI | 8080 |
| Spark Master RPC | 7077 |
| Elasticsearch | 9200 |
| Kibana | 5601 |

## Docker Compose (Alternative)

For development without Kubernetes:

```bash
docker-compose up
```

This starts Postgres, the backend, and the frontend. Spark and Elasticsearch are available via profiles:

```bash
docker-compose --profile spark --profile elastic up
```

## Cluster Management

Create a Kind cluster:

```bash
make create-local-cluster
```

Delete the cluster:

```bash
make delete-local-cluster
```

Deploy all K8s resources:

```bash
make deploy-k8s
```

Delete all K8s resources:

```bash
make k8s-delete
```

Monitor pods:

```bash
make watch-pods
make get_pods
```

View logs:

```bash
make k8s-logs-backend
make k8s-logs-frontend
make k8s-logs-all
```

## Cleanup

Remove all resources:

```bash
make clean-all
```

This deletes the Kind cluster and prunes Docker resources.
