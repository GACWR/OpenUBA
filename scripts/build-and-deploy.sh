#!/bin/bash
# build and deploy script for openuba

set -e

echo "building docker images..."
docker build -f docker/backend.dockerfile -t openuba-backend:latest .
docker build -f docker/frontend.dockerfile -t openuba-frontend:latest .
docker build -f docker/model-runner/Dockerfile -t openuba-model-runner:latest .

echo "loading images into kind cluster..."
kind load docker-image openuba-backend:latest --name openuba-cluster
kind load docker-image openuba-frontend:latest --name openuba-cluster
kind load docker-image openuba-model-runner:latest --name openuba-cluster

echo "deploying to kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n openuba --timeout=300s || true
kubectl apply -f k8s/postgraphile-deployment.yaml
kubectl wait --for=condition=ready pod -l app=postgraphile -n openuba --timeout=300s || true
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/spark-deployment.yaml
kubectl wait --for=condition=ready pod -l app=spark-master -n openuba --timeout=300s || true
kubectl apply -f k8s/elasticsearch-deployment.yaml
kubectl wait --for=condition=ready pod -l app=elasticsearch -n openuba --timeout=300s || true
kubectl apply -f k8s/kibana-deployment.yaml
kubectl apply -f k8s/ingress.yaml

echo "waiting for services to be ready..."
sleep 15

echo "running initial data ingestion..."
kubectl delete job init-data-ingestion -n openuba --ignore-not-found=true || true
kubectl apply -f k8s/init-job.yaml
kubectl wait --for=condition=complete job/init-data-ingestion -n openuba --timeout=600s || true

echo "deployment complete!"
echo "frontend should be available at http://openuba.local or via port-forward"
echo "to port-forward: kubectl port-forward -n openuba service/frontend 3000:3000"

