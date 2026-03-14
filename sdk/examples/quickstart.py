"""
OpenUBA SDK Quickstart Example
==============================

Demonstrates the core SDK workflow:
1. Configure the SDK
2. Register a model
3. Create a dataset
4. Run training
5. Create a visualization
6. Build a dashboard
"""

import openuba

# 1. Configure the SDK (uses env vars by default)
openuba.configure(
    api_url="http://localhost:8000",
    token="your-jwt-token-here",
)

# 2. Register a model
model = openuba.register_model(
    name="login-anomaly-detector",
    framework="sklearn",
    description="Detects anomalous login patterns using Isolation Forest",
)
print(f"Model registered: {model['id']}")

# 3. Create a dataset
dataset = openuba.create_dataset(
    name="auth-logs-2024",
    description="Authentication logs for anomaly detection",
    source_type="upload",
    format="csv",
)
print(f"Dataset created: {dataset['id']}")

# 4. Start training
job = openuba.start_training(
    model_id=model["id"],
    dataset_id=dataset["id"],
    hardware_tier="cpu-small",
    hyperparameters={
        "contamination": 0.05,
        "n_estimators": 200,
        "max_samples": "auto",
    },
    wait=True,
)
print(f"Training completed: {job['status']}")

# 5. Create a visualization
viz = openuba.create_visualization(
    name="Login Anomaly Heatmap",
    backend="matplotlib",
    description="Heatmap of anomalous login times",
)
print(f"Visualization created: {viz['id']}")

# 6. Create a dashboard
dashboard = openuba.create_dashboard(
    name="Security Overview",
    description="Real-time security monitoring dashboard",
    layout=[{
        "title": "Anomaly Distribution",
        "chart_type": "bar",
        "x_key": "hour",
        "y_key": "count",
        "data": [
            {"hour": "00:00", "count": 12},
            {"hour": "06:00", "count": 3},
            {"hour": "12:00", "count": 8},
            {"hour": "18:00", "count": 25},
        ],
    }],
)
print(f"Dashboard created: {dashboard['id']}")

# 7. Query anomalies
anomalies = openuba.query_anomalies(min_risk=0.8, limit=10)
print(f"High-risk anomalies: {len(anomalies)}")

print("\nQuickstart complete!")
