dev-legacy: check run
run:
	cd core/ ; python3.7 core.py ;
check:
	cd core/ ; \
	mypy \
	anomaly.py \
	case.py \
	core.py \
	database.py \
	dataset.py \
	entity.py \
	entity_test.py \
	encode.py \
	encode_test.py \
	model.py \
	process.py \
	risk.py \
	riskmanager.py \
	display.py \
	user.py \
	user_test.py \
	utility.py \
	alert.py \
	api.py \
	hash.py \
	hash_test.py \
	--ignore-missing-imports \
	--explicit-package-bases ;
profile_model:
	cd core/ ; python3.7 core.py profile_model ${model_name};
rd: # react development server
	cd interface/ ; npm run start
rb: # react build
	cd interface/ ; npm run build
electron: # launch electron
	cd interface/ ; npm run start-electron
electron_static: # launch electron static react
	cd interface/ ; npm run start-electron-static
package: #package react
	cd interface/ ; npm run package;
save_dev:
	git add * -v ; git commit -am ${M}-v ; git push origin master:main_dev_branch -v;
# testing - unit and integration tests
test: install-test-deps
	@echo "Running unit and integration tests..."
	pytest core/tests/ -v --tb=short

pytest: test

test-unit:
	@echo "Running unit tests only..."
	pytest core/tests/ -v --tb=short -k "not e2e and not integration"

test-integration:
	@echo "Running integration tests..."
	pytest core/tests/ -v --tb=short -k "integration"

test-api:
	@echo "Running API router tests..."
	pytest core/tests/test_api_routers/ -v --tb=short

test-repositories:
	@echo "Running repository tests..."
	pytest core/tests/test_repositories.py -v --tb=short

test-registry:
	@echo "Running registry tests..."
	pytest core/tests/test_registry/ -v --tb=short

test-services:
	@echo "Running service tests..."
	pytest core/tests/test_services/ -v --tb=short

install-test-deps:
	@echo "Installing testcontainers..."
	pip install 'testcontainers==3.7.0'
	@echo "Installing all requirements..."
	pip install -r requirements.txt
# docker image building - builds all containers
build: build-containers
build-backend:
	docker build -f docker/backend.dockerfile -t openuba-backend:latest .
build-frontend:
	docker build -f docker/frontend.dockerfile -t openuba-frontend:latest .
build-model-runner: build-runner-base build-runner-sklearn build-runner-torch build-runner-tf build-runner-networkx
build-runner-base:
	docker build -f docker/model-runner/Dockerfile.base -t openuba-model-runner:base .
build-runner-sklearn:
	docker build -f docker/model-runner/Dockerfile.sklearn -t openuba-model-runner:sklearn --build-arg BASE_IMAGE=openuba-model-runner:base .
build-runner-torch:
	docker build -f docker/model-runner/Dockerfile.pytorch -t openuba-model-runner:pytorch --build-arg BASE_IMAGE=openuba-model-runner:base .
build-runner-tf:
	docker build -f docker/model-runner/Dockerfile.tensorflow -t openuba-model-runner:tensorflow --build-arg BASE_IMAGE=openuba-model-runner:base .
build-runner-networkx:
	docker build -f docker/model-runner/Dockerfile.networkx -t openuba-model-runner:networkx --build-arg BASE_IMAGE=openuba-model-runner:base .
build-operator:
	docker build -f docker/operator.dockerfile -t openuba-operator:latest .
build-containers: build-backend build-frontend build-model-runner build-operator
	@echo "all containers built successfully"

# load images into kind cluster
load-images:
	@echo "pulling and loading external images..."
	@echo "pulling and loading external images... skipped (letting k8s pull)"
	@echo "loading local images..."
	kind load docker-image openuba-backend:latest --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-frontend:latest --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-model-runner:base --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-model-runner:sklearn --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-model-runner:pytorch --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-model-runner:tensorflow --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-model-runner:networkx --name openuba-cluster || echo "kind cluster not found or not using kind"
	kind load docker-image openuba-operator:latest --name openuba-cluster || echo "kind cluster not found or not using kind"
	@echo "images loaded successfully"

# kubernetes deployment - deploys all services
deploy-operator:
	@echo "deploying operator and crds..."
	kubectl apply -f k8s/crds/
	kubectl apply -f k8s/operator-rbac.yaml
	kubectl apply -f k8s/operator-deployment.yaml
	@echo "operator deployed"

deploy-k8s:
	@echo "deploying all kubernetes resources..."
	kubectl apply -f k8s/namespace.yaml
	$(MAKE) deploy-operator
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/dev-pv.yaml
	kubectl apply -f k8s/postgres.yaml
	kubectl wait --for=condition=ready pod -l app=postgres -n openuba --timeout=300s || true
	kubectl apply -f k8s/backend-rbac.yaml
	kubectl apply -f k8s/postgraphile-deployment.yaml
	kubectl wait --for=condition=ready pod -l app=postgraphile -n openuba --timeout=300s || true
	kubectl apply -f k8s/datasets-pv.yaml
	kubectl apply -f k8s/frontend-source-pv.yaml
	kubectl apply -f k8s/source-code-pv.yaml
	kubectl apply -f k8s/metastore-pv.yaml
	kubectl apply -f k8s/saved-models-pv.yaml
	kubectl apply -f k8s/backend-deployment.yaml
	kubectl apply -f k8s/frontend-deployment.yaml
	kubectl apply -f k8s/spark-deployment.yaml
	kubectl wait --for=condition=ready pod -l app=spark-master -n openuba --timeout=300s || true
	kubectl apply -f k8s/elasticsearch-deployment.yaml
	kubectl wait --for=condition=ready pod -l app=elasticsearch -n openuba --timeout=300s || true
	kubectl apply -f k8s/ingress.yaml
	@echo "waiting for all services to be ready..."
	@sleep 15
	@echo "running initial data ingestion..."
	@$(MAKE) k8s-init-data || echo "data ingestion job failed or already completed"
	@echo "deployment complete!"

deploy-dashboard:
	@echo "Deploying Kubernetes Dashboard..."
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
	@echo "Creating Admin User..."
	kubectl apply -f k8s/dashboard-admin.yaml
	@echo "Waiting for dashboard to be ready..."
	kubectl wait --for=condition=ready pod -l k8s-app=kubernetes-dashboard -n kubernetes-dashboard --timeout=300s || true
	@echo "Generating Admin Token..."
	@kubectl create token admin-user -n kubernetes-dashboard --duration=8760h > dashboard_token.txt
	@echo "Token saved to dashboard_token.txt"
	@echo "To access the dashboard:"
	@echo "1. Run 'kubectl proxy'"
	@echo "2. Visit: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
	@echo "3. Use the token from dashboard_token.txt to login"

k8s-proxy:
	@echo "Starting Kubernetes Proxy..."
	@echo "Dashboard: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
	@kubectl proxy

# hybrid development - run backend/frontend locally, infra in k8s
dev-hybrid:
	@echo "Setting up hybrid development environment..."
	@echo "Port forwarding infrastructure services..."
	@trap 'kill %1 %2 %3 %4' SIGINT
	@kubectl port-forward svc/postgres 5432:5432 -n openuba & \
	kubectl port-forward svc/spark-master 7077:7077 -n openuba & \
	kubectl port-forward svc/spark-master 8080:8080 -n openuba & \
	kubectl port-forward svc/elasticsearch 9200:9200 -n openuba & \
	kubectl port-forward svc/postgraphile 5001:5000 -n openuba & \
	echo "Services forwarded:" && \
	echo "- Postgres: localhost:5432" && \
	echo "- Spark Master: localhost:7077 (UI: 8080)" && \
	echo "- Elasticsearch: localhost:9200" && \
	echo "Ready for local backend/frontend development!" && \
	wait

# demo mode - forward EVERYTHING including frontend/backend
# 	kubectl port-forward svc/frontend 3000:3000 -n openuba & \
# 	kubectl port-forward svc/backend 8000:8000 -n openuba & 
k8s-forward:
	@echo "Setting up full demo environment..."
	@echo "Port forwarding ALL services..."
	@trap 'kill %1 %2 %3 %4 %5 %6 %7' SIGINT
	@kubectl port-forward svc/postgres 5432:5432 -n openuba & \
	kubectl port-forward svc/frontend 3000:3000 -n openuba & \
	kubectl port-forward svc/backend 8000:8000 -n openuba & \
	kubectl port-forward svc/postgraphile 5001:5000 -n openuba & \
	kubectl port-forward svc/spark-master 7077:7077 -n openuba & \
	kubectl port-forward svc/spark-master 8080:8080 -n openuba & \
	kubectl port-forward svc/elasticsearch 9200:9200 -n openuba & \
	echo "Services forwarded:" && \
	echo "- Frontend: http://localhost:3000" && \
	echo "- Backend: http://localhost:8000" && \
	echo "- Postgres: localhost:5432" && \
	echo "- PostGraphile: localhost:5000" && \
	echo "- Spark Master: localhost:7077 (UI: 8080)" && \
	echo "- Elasticsearch: localhost:9200" && \
	echo "Ready for demo! Press Ctrl+C to stop." && \
	wait

# e2e - full reset and demo
k8s-e2e:
	@echo "Starting full E2E reset..."
	@$(MAKE) delete-local-cluster
	@$(MAKE) create-local-cluster
	@$(MAKE) k8s-deploy
	@$(MAKE) deploy-dashboard
	@$(MAKE) k8s-forward

######## legacy alias for backward compatibility
k8s-deploy: build-containers load-images deploy-k8s

k8s-delete:
	kubectl delete -f k8s/ingress.yaml || true
	kubectl delete -f k8s/frontend-deployment.yaml || true
	kubectl delete -f k8s/backend-deployment.yaml || true
	kubectl delete -f k8s/elasticsearch-deployment.yaml || true
	kubectl delete -f k8s/spark-deployment.yaml || true
	kubectl delete -f k8s/postgraphile-deployment.yaml || true
	kubectl delete -f k8s/init-job.yaml || true
	kubectl delete -f k8s/postgres.yaml || true
	kubectl delete -f k8s/secrets.yaml || true
	kubectl delete -f k8s/namespace.yaml || true
k8s-logs-backend:
	kubectl logs -f -l app=backend -n openuba
k8s-logs-frontend:
	kubectl logs -f -l app=frontend -n openuba
k8s-logs-spark:
	kubectl logs -f -l app=spark-master -n openuba || kubectl logs -f -l app=spark-worker -n openuba
k8s-logs-elasticsearch:
	kubectl logs -f -l app=elasticsearch -n openuba
k8s-logs-postgraphile:
	kubectl logs -f -l app=postgraphile -n openuba
k8s-init-data:
	@echo "Triggering data ingestion via API..."
	@kubectl exec -n openuba deploy/backend -- curl -X POST http://localhost:8000/api/v1/data/ingest \
		-H "Content-Type: application/json" \
		-d '{"dataset_name": "toy_1", "ingest_to_spark": true, "ingest_to_es": true}'
	@echo "Data ingestion triggered. Check logs or UI for status."
k8s-logs-all:
	@echo "Viewing logs for all services (use Ctrl+C to exit)..."
	@kubectl logs -f -l app=backend -n openuba & \
	kubectl logs -f -l app=frontend -n openuba & \
	kubectl logs -f -l app=spark-master -n openuba & \
	kubectl logs -f -l app=elasticsearch -n openuba & \
	kubectl logs -f -l app=postgraphile -n openuba & \
	wait
create-local-cluster:
	kind create cluster --name openuba-cluster --config configs/local.yaml
delete-local-cluster:
	kind delete cluster --name openuba-cluster
# e2e testing - requires kubernetes deployment
e2e-setup:
	@echo "Installing Playwright and E2E dependencies..."
	pip install -r requirements.txt
	playwright install chromium
	@echo "E2E setup complete"

e2e-deploy: build-containers
	@echo "Deploying to Kubernetes for E2E testing..."
	$(MAKE) k8s-deploy
	@echo "Waiting for all pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app=postgres -n openuba --timeout=300s || true
	@kubectl wait --for=condition=ready pod -l app=backend -n openuba --timeout=300s || true
	@kubectl wait --for=condition=ready pod -l app=frontend -n openuba --timeout=300s || true
	@echo "Deployment ready for E2E tests"

e2e-test:
	@echo "Running E2E tests (requires k8s deployment - use 'make e2e-deploy' first)..."
	pytest core/tests/e2e/ -v --tb=short

e2e-test-models:
	@echo "Running E2E model management tests..."
	venv/bin/pytest core/tests/e2e/test_models_flow.py -v --tb=short

e2e-test-anomalies:
	@echo "Running E2E anomaly tests..."
	pytest core/tests/e2e/test_anomalies_flow.py -v --tb=short

e2e-test-cases:
	@echo "Running E2E case management tests..."
	pytest core/tests/e2e/test_cases_flow.py -v --tb=short

e2e-test-rules:
	@echo "Running E2E rules tests..."
	pytest core/tests/e2e/test_rules_flow.py -v --tb=short

e2e-test-display:
	@echo "Running E2E display/dashboard tests..."
	pytest core/tests/e2e/test_display_flow.py -v --tb=short

e2e-cleanup:
	@echo "Cleaning up E2E deployment..."
	$(MAKE) k8s-delete

e2e-full: e2e-setup e2e-deploy
	@echo "Running full E2E test suite..."
	$(MAKE) e2e-test || ($(MAKE) e2e-cleanup && exit 1)
	$(MAKE) e2e-cleanup

# run all tests (unit + e2e)
test-all: test e2e-full
	@echo "All tests completed"

# local development
# database initialization
init-db:
	@echo "Initializing database schema..."
	@python core/db/init_schema.py

init-db-local:
	@echo "Initializing database schema with local postgres..."
	@DATABASE_URL=postgresql://gacwr:test1234@localhost:5432/openuba python core/db/init_schema.py

init-db-k8s:
	@echo "Initializing database schema in Kubernetes..."
	@kubectl exec -n openuba -it $$(kubectl get pod -n openuba -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U gacwr -d openuba -f /dev/stdin < core/db/schema.sql || echo "Schema initialization via kubectl exec"

# unified local development command - runs everything
dev: init-db-local
	@echo "Starting local development environment..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "GraphQL will run on http://localhost:5000"
	@echo "Press Ctrl+C to stop all services"
	@bash -c ' \
	trap "kill $$BACKEND_PID $$FRONTEND_PID 2>/dev/null; exit" INT TERM EXIT; \
	mkdir -p .openuba/logs; \
	$(MAKE) dev-backend > .openuba/logs/backend.log 2>&1 & \
	BACKEND_PID=$$!; \
	echo $$BACKEND_PID > .openuba/logs/backend.pid; \
	echo "Backend started (PID: $$BACKEND_PID) -> .openuba/logs/backend.log"; \
	sleep 3; \
	$(MAKE) dev-frontend > .openuba/logs/frontend.log 2>&1 & \
	FRONTEND_PID=$$!; \
	echo $$FRONTEND_PID > .openuba/logs/frontend.pid; \
	echo "Frontend started (PID: $$FRONTEND_PID) -> .openuba/logs/frontend.log"; \
	wait'

# local development - run services individually
dev-local: dev
	@echo "Note: dev-local is now an alias for dev"

setup-backend:
	@echo "Setting up backend environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@venv/bin/pip install -r requirements.txt
	@echo "Backend environment ready."

dev-backend: setup-backend
	@echo "Starting backend server..."
	@JAVA_HOME=$$([ -d "/opt/homebrew/opt/openjdk@17" ] && echo "/opt/homebrew/opt/openjdk@17" || echo "$$JAVA_HOME") \
	PATH="/opt/homebrew/opt/openjdk@17/bin:$$PATH" \
	DATABASE_URL=postgresql://gacwr:gacwr@localhost:5432/openuba \
	ENABLE_GRAPHQL=false \
	POSTGRAPHILE_HOST=0.0.0.0 \
	POSTGRAPHILE_PORT=5001 \
	SPARK_MASTER_URL=local[*] \
	ELASTICSEARCH_HOST=http://localhost:9200 \
	EXECUTION_MODE=docker \
	CORS_ORIGINS=http://localhost:3000,http://localhost:3001 \
	venv/bin/uvicorn core.fastapi_app:app --host 0.0.0.0 --port 8000 --reload

dev-install-frontend:
	@echo "Installing frontend dependencies..."
	@cd interface && pnpm install || (echo "pnpm not found, trying npm..." && npm install --legacy-peer-deps)

dev-frontend: dev-install-frontend
	@echo "Starting frontend development server..."
	@cd interface && \
	NEXT_PUBLIC_API_URL=http://localhost:8000 \
	NEXT_PUBLIC_GRAPHQL_URL=http://localhost:5001/graphql \
	pnpm dev || (echo "pnpm not found, trying npm..." && npm run dev)

dev-restart-backend:
	@echo "Rebuilding and redeploying backend..."
	$(MAKE) build-backend
	kind load docker-image openuba-backend:latest --name openuba-cluster
	kubectl rollout restart deployment backend -n openuba
	kubectl rollout status deployment backend -n openuba --timeout=120s
	@echo "Backend redeployed."

dev-restart-frontend:
	@echo "Rebuilding and redeploying frontend..."
	$(MAKE) build-frontend
	kind load docker-image openuba-frontend:latest --name openuba-cluster
	kubectl rollout restart deployment frontend -n openuba
	kubectl rollout status deployment frontend -n openuba --timeout=120s
	@echo "Frontend redeployed."

dev-restart-operator:
	@echo "Re-applying CRDs, RBAC, and restarting operator..."
	kubectl apply -f k8s/crds/
	kubectl apply -f k8s/operator-rbac.yaml
	kubectl apply -f k8s/backend-rbac.yaml
	kubectl rollout restart deployment openuba-operator -n openuba
	kubectl rollout status deployment openuba-operator -n openuba --timeout=120s
	@echo "Operator restarted."

dev-restart-backend-local:
	@echo "Restarting local backend..."
	@-pkill -f "uvicorn core.fastapi_app" 2>/dev/null || true
	@sleep 1
	$(MAKE) dev-backend

dev-restart-frontend-local:
	@echo "Restarting local frontend..."
	@-pkill -f "next dev" 2>/dev/null || true
	@-pkill -f "next-router-worker" 2>/dev/null || true
	@sleep 1
	$(MAKE) dev-frontend

dev-postgres:
	@echo "Starting local postgres container (optional if you have local postgres)..."
	@docker run -d --name openuba-postgres-local \
		-e POSTGRES_USER=gacwr \
		-e POSTGRES_PASSWORD=test1234 \
		-e POSTGRES_DB=openuba \
		-p 5432:5432 \
		postgres:15-alpine || echo "Postgres container already running or port in use"

dev-stop:
	@echo "Stopping local postgres container..."
	@docker stop openuba-postgres-local || true
	@docker rm openuba-postgres-local || true
	@echo "Local services stopped"

clean-docker:
	@echo "Cleaning up unused Docker resources..."
	@docker system prune -f
	@echo "Docker cleanup complete"

clean-all: delete-local-cluster clean-docker
	@echo "Full cleanup complete"


clean-logs:
	@echo "Cleaning up logs..."
	@rm -f *.log *.pid *.txt
	@rm -rf .openuba/logs/*
	@echo "Logs cleaned"

e2e-dev:
	make delete-local-cluster
	make create-local-cluster      
	sleep 120                          
	make k8s-deploy 
	sleep 120
	make k8s-forward
	make dev-backend
	make dev-frontend

watch-pods:
	@echo "Watching pods..."
	@kubectl get pods -n openuba -w

reset-dev: 
	make delete-local-cluster 
	make create-infra
	

create-infra:
	./scripts/start-dev.sh

get_trainings:
	kubectl get ubatrainings -n openuba

get_pods:
	kubectl get pods -n openuba

redeploy-db:
	@echo "Redeploying Postgres with new credentials (gacwr)..."
	@kubectl delete secret postgres-secret backend-secret -n openuba || true
	@kubectl delete -f k8s/postgres.yaml || true
	@echo "Applying new configuration..."
	@kubectl apply -f k8s/secrets.yaml
	@kubectl apply -f k8s/postgres.yaml
	@echo "Waiting for Postgres to be ready..."
	@kubectl wait --for=condition=ready pod -l app=postgres -n openuba --timeout=300s
	@echo "Postgres redeployed! You can now connect with user: gacwr, password: gacwr"

# =====================================================================
#  SDK — Python Package (PyPI)
# =====================================================================

SDK_DIR := sdk

# Set version: make sdk-publish VERSION=0.2.0
ifdef VERSION
sdk-set-version:
	@echo "Setting version to $(VERSION)..."
	@sed -i '' 's/^version = ".*"/version = "$(VERSION)"/' $(SDK_DIR)/pyproject.toml
	@sed -i '' 's/^__version__ = ".*"/__version__ = "$(VERSION)"/' $(SDK_DIR)/src/openuba/__init__.py
	@echo "Version set to $(VERSION)"
else
sdk-set-version:
	@true
endif

sdk-build: sdk-set-version sdk-clean ## Build the openuba Python package (VERSION=x.y.z)
	@echo "Building openuba SDK..."
	cd $(SDK_DIR) && python3 -m pip install --upgrade build --quiet && python3 -m build
	@echo "Build artifacts:"
	@ls -lh $(SDK_DIR)/dist/

sdk-publish-test: sdk-build ## Publish openuba to TestPyPI (VERSION=x.y.z)
	@echo "Uploading to TestPyPI..."
	cd $(SDK_DIR) && python3 -m pip install --upgrade twine --quiet && python3 -m twine upload --repository testpypi dist/*
	@echo "Done! Install with: pip install --index-url https://test.pypi.org/simple/ openuba"

sdk-publish: sdk-build ## Publish openuba to PyPI (VERSION=x.y.z)
	@echo "Uploading to PyPI..."
	cd $(SDK_DIR) && python3 -m pip install --upgrade twine --quiet && python3 -m twine upload dist/*
	@echo "Done! Install with: pip install openuba"

sdk-clean: ## Remove SDK build artifacts
	rm -rf $(SDK_DIR)/dist/ $(SDK_DIR)/build/ $(SDK_DIR)/*.egg-info
