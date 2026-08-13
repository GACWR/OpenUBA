#!/bin/bash
# scripts/start-dev.sh
# Automates the full OpenUBA dev environment setup.
set -e # Exit immediately if a command exits with a non-zero status.

# Ensure we are in the project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "🚀 Starting OpenUBA Dev Environment..."
echo "1. Infrastructure Setup (This may take a few minutes)..."

# Step 1: Clean & Create
make delete-local-cluster || true # Ignore error if cluster doesn't exist

echo "🗑️ Cleaning up Docker images..."
for img in openuba-backend:latest \
           openuba-frontend:latest \
           openuba-operator:latest \
           openuba-model-runner:base \
           openuba-model-runner:sklearn \
           openuba-model-runner:pytorch \
           openuba-model-runner:tensorflow \
           openuba-model-runner:networkx; do
    docker rmi "$img" 2>/dev/null || true
done
echo "🧹 Removing dangling images from previous builds..."
docker image prune -f 2>/dev/null || true

echo "✨ Creating new cluster..."
make create-local-cluster

echo "📦 Building and Loading Images..."
make build-containers
make load-images

echo "🏗️ Deploying Kubernetes Resources..."
make deploy-k8s

echo "✅ Infrastructure Ready!"

# Step 2: Kill stale port-forwards, then start fresh ones.
# On macOS we open a dedicated Terminal window (via `open -a Terminal.app`,
# which needs no accessibility permissions). On Linux — including headless
# servers where there is no `open`/Terminal.app — we run the port-forwards in
# the background and tee their output to port-forward.log instead.
echo "🔌 Starting port-forwards..."
pkill -f "kubectl.*port-forward.*openuba" 2>/dev/null || true
sleep 1

if [ "$(uname)" = "Darwin" ]; then
    open -a Terminal.app "$PROJECT_ROOT/scripts/port-forward.sh"
    PF_LOCATION="separate Terminal window"
else
    nohup bash "$PROJECT_ROOT/scripts/port-forward.sh" \
        > "$PROJECT_ROOT/port-forward.log" 2>&1 &
    PF_LOCATION="background (logs: port-forward.log)"
fi

# Wait for port-forwards to establish
echo "   Waiting for services..."
RETRIES=0
until curl -s -o /dev/null http://localhost:8000/docs 2>/dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge 20 ]; then
        echo "⚠️  Warning: backend not reachable on port 8000 after 20s"
        break
    fi
    sleep 1
done

if [ $RETRIES -lt 20 ]; then
    echo "   ✓ All services reachable"
fi

echo ""
echo "🎉 OpenUBA is ready!"
echo "  Frontend:      http://localhost:3000"
echo "  Backend:       http://localhost:8000"
echo "  PostGraphile:  http://localhost:5001/graphql"
echo "  Spark UI:      http://localhost:8080"
echo ""
echo "  Port-forwards running in ${PF_LOCATION}."
echo "  Stop them with: pkill -f 'kubectl.*port-forward.*openuba'"
