#!/bin/bash
# scripts/port-forward.sh
# Starts kubectl port-forwards as background processes.
# Cleans up spawned processes on exit/interrupt.

PIDS=()

cleanup() {
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait 2>/dev/null
}

trap cleanup EXIT INT TERM

pkill -f "kubectl.*port-forward.*openuba" 2>/dev/null || true
sleep 1

kubectl port-forward svc/postgres 5432:5432 -n openuba &
PIDS+=($!)
kubectl port-forward svc/frontend 3000:3000 -n openuba &
PIDS+=($!)
kubectl port-forward svc/backend 8000:8000 -n openuba &
PIDS+=($!)
kubectl port-forward svc/postgraphile 5001:5000 -n openuba &
PIDS+=($!)
kubectl port-forward svc/spark-master 7077:7077 -n openuba &
PIDS+=($!)
kubectl port-forward svc/spark-master 8080:8080 -n openuba &
PIDS+=($!)
kubectl port-forward svc/elasticsearch 9200:9200 -n openuba &
PIDS+=($!)

# Keep this process alive so children stay alive
wait
