# Docker Build Guide

OpenUBA uses Docker images for all services, deployed to a local Kind (Kubernetes in Docker) cluster for development. This document covers the container build system, image hierarchy, and deployment workflow.

## Images

| Image | Dockerfile | Purpose |
|-------|-----------|---------|
| openuba-backend:latest | docker/backend.dockerfile | FastAPI backend + PostGraphile |
| openuba-frontend:latest | docker/frontend.dockerfile | Next.js frontend |
| openuba-operator:latest | docker/operator.dockerfile | Kopf-based CRD controller |
| openuba-model-runner:base | docker/model-runner/Dockerfile.base | Base runner with PySpark + common deps |
| openuba-model-runner:sklearn | docker/model-runner/Dockerfile.sklearn | scikit-learn runtime |
| openuba-model-runner:pytorch | docker/model-runner/Dockerfile.pytorch | PyTorch runtime |
| openuba-model-runner:tensorflow | docker/model-runner/Dockerfile.tensorflow | TensorFlow + Keras runtime |
| openuba-model-runner:networkx | docker/model-runner/Dockerfile.networkx | NetworkX graph runtime |

## Build Commands

All builds are run through the Makefile.

Build everything:

```bash
make build-containers
```

Build individual images:

```bash
make build-backend
make build-frontend
make build-operator
make build-model-runner    # builds base + all variants
```

Build individual runner variants:

```bash
make build-runner-base
make build-runner-sklearn
make build-runner-torch
make build-runner-tf
make build-runner-networkx
```

## Image Details

### Backend

- **Base**: python:3.9-slim
- **Includes**: gcc, postgresql-client, curl, Node.js, npm, default-jre
- **PostGraphile**: Installed globally via npm
- **Workdir**: /app
- **Copies**: core/, scripts/, test_datasets/
- **Exposes**: 8000
- **Entrypoint**: uvicorn core.fastapi_app:app

### Frontend

- **Multi-stage build** (4 stages: base, deps, builder, runner)
- **Base**: node:18-alpine
- **Final stage**: Runs as non-root `nextjs` user
- **Exposes**: 3000
- **Entrypoint**: node server.js

### Operator

- **Base**: python:3.9-slim
- **Installs**: kopf, kubernetes, pyyaml
- **Copies**: core/operator/main.py
- **Entrypoint**: kopf run /app/main.py --verbose

### Model Runner (Base)

- **Base**: python:3.9-slim
- **Includes**: git, curl, default-jre-headless (for PySpark)
- **Copies**: docker/model-runner/runner.py
- **User**: modelrunner (non-root, UID 1000)
- **Workdir**: /app
- **Entrypoint**: python runner.py

### Model Runner Variants

Each variant extends the base image and adds framework-specific dependencies:

- **sklearn**: scikit-learn, joblib
- **pytorch**: torch, torchvision
- **tensorflow**: tensorflow, keras
- **networkx**: networkx

The base image tag is passed via the `BASE_IMAGE` build argument.

## Kind Cluster Workflow

OpenUBA runs on a local Kind cluster. Images are built on the host and loaded into the cluster (no registry push required).

### Full workflow (automated)

```bash
make reset-dev
```

This runs `scripts/start-dev.sh` which:
1. Deletes any existing Kind cluster
2. Creates a new cluster from `configs/local.yaml`
3. Builds all container images
4. Loads images into the Kind cluster
5. Deploys all Kubernetes resources
6. Opens terminal tabs for port forwarding, backend, and frontend

### Manual steps

Create the cluster:

```bash
make create-local-cluster
```

Build and load images:

```bash
make build-containers
make load-images
```

Deploy resources:

```bash
make deploy-k8s
```

Forward ports to localhost:

```bash
make k8s-forward
```

### Rebuilding after code changes

Restart a single service after changes:

```bash
make dev-restart-backend     # rebuild image, load, rollout restart
make dev-restart-frontend    # rebuild image, load, rollout restart
make dev-restart-operator    # rebuild image, load, rollout restart
```

## Kind Cluster Configuration

`configs/local.yaml` defines a single control-plane node:

- Port mappings: 80 (HTTP), 443 (HTTPS) forwarded to host
- Extra mount: Repository root mounted at `/mnt/openuba/root` on the node

This mount allows PersistentVolumes to reference host files directly, so source code, datasets, and model artifacts are shared between the host and cluster pods.

## Docker Compose (Alternative)

For non-Kubernetes local development, `docker-compose.yml` provides:

| Service | Port | Profile |
|---------|------|---------|
| postgres | 5432 | default |
| backend | 8000 | default |
| frontend | 3000 | default |
| spark-master | 8080, 7077 | spark |
| spark-worker | - | spark |
| elasticsearch | 9200 | elastic |
| kibana | 5601 | elastic |

Start core services:

```bash
docker-compose up
```

Start with Spark:

```bash
docker-compose --profile spark up
```

Start with Elasticsearch and Kibana:

```bash
docker-compose --profile elastic up
```

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://... | Postgres connection string |
| EXECUTION_MODE | docker | `docker` or `kubernetes` |
| ENABLE_GRAPHQL | true | Enable PostGraphile subprocess |
| POSTGRAPHILE_HOST | 0.0.0.0 | PostGraphile bind address |
| POSTGRAPHILE_PORT | 5000 | PostGraphile port |
| MODEL_STORAGE_PATH | /app/core/model_library | Model code storage |
| CORS_ORIGINS | http://localhost:3000 | Allowed CORS origins |
| ELASTICSEARCH_HOST | elasticsearch | ES hostname |
| SPARK_MASTER_URL | spark://spark-master:7077 | Spark master |
| OLLAMA_HOST | - | Ollama LLM endpoint |
| OLLAMA_MODEL | - | Default Ollama model |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| NEXT_PUBLIC_API_URL | http://localhost:8000 | Backend API URL |
| NEXT_PUBLIC_GRAPHQL_URL | http://localhost:5000/graphql | GraphQL endpoint |

## Troubleshooting

Check pod status:

```bash
make get_pods
```

View logs:

```bash
make k8s-logs-backend
make k8s-logs-frontend
make k8s-logs-spark
make k8s-logs-elasticsearch
make k8s-logs-postgraphile
make k8s-logs-all
```

Watch pods in real time:

```bash
make watch-pods
```

If images fail to load into Kind, ensure the cluster is running:

```bash
kind get clusters
```

If a pod is in CrashLoopBackOff, check logs and redeploy:

```bash
kubectl logs -n openuba <pod-name>
make dev-restart-backend
```
