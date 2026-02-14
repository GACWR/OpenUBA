#!/bin/bash
# scripts/start-dev.sh
# Automates the 4-terminal workflow for OpenUBA hybrid development.
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

# Function to open a new tab and run a command (macOS Terminal)
open_tab() {
    local title="$1"
    local cmd="$2"
    
    osascript -e "
        tell application \"Terminal\"
            activate
            tell application \"System Events\" to keystroke \"t\" using command down
            repeat while contents of selected tab of window 1 starts with \" \"
                delay 0.01
            end repeat
            do script \"cd \\\"$PROJECT_ROOT\\\" && echo \\\"Starting $title...\\\" && $cmd\" in front window
        end tell
    "
}

echo "🚀 Launching services in new tabs..."

# Tab 1: Port Forwarding
# open_tab "Hybrid Networking" "make dev-hybrid"
open_tab "K8s Networking" "make k8s-forward"

# Tab 2: Backend - this runs a local version of backend on the host
open_tab "Local Backend" "make dev-backend"

# Tab 3: Frontend - this runs a local version of frontend on the host
open_tab "Local Frontend" "make dev-frontend"

echo "🎉 All services launched!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Monitor the tabs for logs."
