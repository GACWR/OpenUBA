"""
OpenUBA Pipeline Example
========================

Demonstrates how to create and run a multi-step pipeline:
1. Data preprocessing (training step)
2. Model training
3. Model inference/evaluation
"""

import openuba

openuba.configure(api_url="http://localhost:8000")

# 1. Create a pipeline with multiple steps
pipeline = openuba.create_pipeline(
    name="full-uba-pipeline",
    description="End-to-end UBA pipeline: preprocess -> train -> infer",
    steps=[
        {
            "type": "training",
            "model_id": "data-preprocessor-model-id",
            "hardware_tier": "cpu-small",
            "hyperparameters": {
                "normalize": True,
                "fill_na": "median",
            },
        },
        {
            "type": "training",
            "model_id": "isolation-forest-model-id",
            "dataset_id": "auth-logs-dataset-id",
            "hardware_tier": "cpu-large",
            "hyperparameters": {
                "contamination": 0.05,
                "n_estimators": 200,
            },
        },
        {
            "type": "inference",
            "model_id": "isolation-forest-model-id",
            "dataset_id": "live-auth-logs-dataset-id",
            "hardware_tier": "cpu-small",
        },
    ],
)
print(f"Pipeline created: {pipeline['id']}")
print(f"Steps: {len(pipeline.get('steps', []))}")

# 2. Run the pipeline
result = openuba.run_pipeline(pipeline["id"])
print(f"\nPipeline run started: {result}")

# 3. Monitor with job polling (if wait=True is supported)
print("\nPipeline submitted for execution.")
print("Monitor progress in the OpenUBA UI at /pipelines")
