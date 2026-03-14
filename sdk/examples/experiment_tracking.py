"""
OpenUBA Experiment Tracking Example
====================================

Demonstrates how to:
1. Create an experiment
2. Run multiple training configurations
3. Compare results
4. Select the best model
"""

import openuba

openuba.configure(api_url="http://localhost:8000")

# 1. Create an experiment
experiment = openuba.create_experiment(
    name="isolation-forest-tuning",
    description="Hyperparameter tuning for login anomaly detection",
)
print(f"Experiment created: {experiment['id']}")

# 2. Define hyperparameter configurations to test
configs = [
    {"contamination": 0.01, "n_estimators": 100, "max_samples": 256},
    {"contamination": 0.05, "n_estimators": 200, "max_samples": 512},
    {"contamination": 0.10, "n_estimators": 300, "max_samples": "auto"},
]

# 3. Run each configuration
for i, config in enumerate(configs):
    print(f"\nRunning config {i + 1}/{len(configs)}: {config}")

    # Create hyperparameter set
    hparams = openuba.create_hyperparameters(
        name=f"iforest-config-{i + 1}",
        parameters=config,
        description=f"Config {i + 1} for isolation forest tuning",
    )

    # Start training with these hyperparameters
    job = openuba.start_training(
        model_id="your-model-id",
        hardware_tier="cpu-small",
        hyperparameters=config,
    )

    # Add run to experiment with simulated metrics
    run = openuba.add_experiment_run(
        experiment_id=experiment["id"],
        job_id=job.get("id"),
        parameters=config,
        metrics={
            "precision": 0.85 + i * 0.03,
            "recall": 0.90 - i * 0.02,
            "f1_score": 0.87 + i * 0.01,
            "auc_roc": 0.92 + i * 0.02,
        },
    )
    print(f"  Run added: {run['id']}")

# 4. Compare all runs
comparison = openuba.compare_experiment_runs(experiment["id"])
print(f"\nExperiment comparison: {len(comparison)} runs")
for run in comparison:
    metrics = run.get("metrics", {})
    params = run.get("parameters", {})
    print(f"  contamination={params.get('contamination')}: "
          f"F1={metrics.get('f1_score', 'N/A')}, AUC={metrics.get('auc_roc', 'N/A')}")

print("\nExperiment tracking complete!")
