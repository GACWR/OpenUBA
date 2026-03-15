"""OpenUBA SDK — install, run, and manage user behavior analytics models."""

from openuba.client import OpenUBAClient
from openuba.visualization import VisualizationContext, render
from openuba.context import ModelContext

__version__ = "0.1.0"

# Module-level client singleton
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenUBAClient()
    return _client


def configure(api_url=None, token=None, registry_url=None, model_dir=None):
    """Configure the OpenUBA SDK client."""
    global _client
    _client = OpenUBAClient(
        api_url=api_url,
        token=token,
        registry_url=registry_url,
        model_dir=model_dir,
    )


def install(model_name, version=None, source=None):
    """Install a model from the openuba-model-hub registry."""
    return _get_client().install_model(model_name, version=version, source=source)


def uninstall(model_name):
    """Remove a locally installed model."""
    return _get_client().uninstall_model(model_name)


def run(model_name, data=None, parameters=None):
    """Run an installed model locally."""
    return _get_client().run_model(model_name, data=data, parameters=parameters)


def list_models(source=None):
    """List models available in the openuba-model-hub registry."""
    return _get_client().list_models(source=source)


def list_installed():
    """List locally installed models."""
    return _get_client().list_installed()


def get_model(model_name):
    """Get details for a specific model."""
    return _get_client().get_model(model_name)


# ─── Model Registration ────────────────────────────────────────────


def register_model(name, model=None, framework=None, description=None):
    """Register a model with the platform."""
    return _get_client().register_model(name, model=model, framework=framework,
                                        description=description)


def publish_version(model_id, version=None, summary=None):
    """Publish a new version of a model."""
    return _get_client().publish_version(model_id, version=version, summary=summary)


def load_model(name_or_id, version=None):
    """Load a model by name or ID."""
    return _get_client().load_model(name_or_id, version=version)


# ─── Dataset Management ────────────────────────────────────────────


def list_datasets():
    """List all datasets."""
    return _get_client().list_datasets()


def get_dataset(dataset_id):
    """Get dataset by ID."""
    return _get_client().get_dataset(dataset_id)


def create_dataset(name, description=None, source_type="upload", format="csv"):
    """Create a dataset record."""
    return _get_client().create_dataset(name, description=description,
                                        source_type=source_type, format=format)


# ─── Jobs ───────────────────────────────────────────────────────────


def start_training(model_id, dataset_id=None, hardware_tier="cpu-small",
                   hyperparameters=None, wait=False):
    """Start a training job."""
    return _get_client().start_training(model_id, dataset_id=dataset_id,
                                        hardware_tier=hardware_tier,
                                        hyperparameters=hyperparameters, wait=wait)


def start_inference(model_id, dataset_id=None, hardware_tier="cpu-small", wait=False):
    """Start an inference job."""
    return _get_client().start_inference(model_id, dataset_id=dataset_id,
                                         hardware_tier=hardware_tier, wait=wait)


def get_job(job_id):
    """Get job details."""
    return _get_client().get_job(job_id)


def wait_for_job(job_id, poll_interval=2, timeout=3600):
    """Wait for a job to complete."""
    return _get_client().wait_for_job(job_id, poll_interval=poll_interval,
                                      timeout=timeout)


def get_logs(job_id):
    """Get job logs."""
    return _get_client().get_logs(job_id)


def post_log(job_id, message, level="info"):
    """Post a log entry for a job."""
    return _get_client().post_log(job_id, message, level=level)


# ─── Visualizations ────────────────────────────────────────────────


def create_visualization(name, backend="matplotlib", description=None, output_type=None,
                         figure=None):
    """Create a visualization. Pass a figure object to auto-render it."""
    return _get_client().create_visualization(name, backend=backend,
                                               description=description,
                                               output_type=output_type,
                                               figure=figure)


def update_visualization(viz_id, rendered_output=None, code=None, data=None, config=None):
    """Update a visualization with rendered output or other fields."""
    return _get_client().update_visualization(viz_id, rendered_output=rendered_output,
                                              code=code, data=data, config=config)


def publish_visualization(viz_id):
    """Publish a visualization."""
    return _get_client().publish_visualization(viz_id)


def list_visualizations():
    """List all visualizations."""
    return _get_client().list_visualizations()


# ─── Dashboards ─────────────────────────────────────────────────────


def create_dashboard(name, layout=None, description=None):
    """Create a dashboard."""
    return _get_client().create_dashboard(name, layout=layout, description=description)


def update_dashboard(dashboard_id, layout=None, name=None):
    """Update a dashboard."""
    return _get_client().update_dashboard(dashboard_id, layout=layout, name=name)


def list_dashboards():
    """List all dashboards."""
    return _get_client().list_dashboards()


# ─── Features ───────────────────────────────────────────────────────


def create_features(feature_names, group_name, description=None, entity="default"):
    """Create a feature group with features."""
    return _get_client().create_features(feature_names, group_name,
                                         description=description, entity=entity)


def load_features(group_name):
    """Load feature group by name."""
    return _get_client().load_features(group_name)


# ─── Experiments ────────────────────────────────────────────────────


def create_experiment(name, description=None):
    """Create an experiment."""
    return _get_client().create_experiment(name, description=description)


def add_experiment_run(experiment_id, job_id=None, model_id=None,
                       parameters=None, metrics=None):
    """Add a run to an experiment."""
    return _get_client().add_experiment_run(experiment_id, job_id=job_id,
                                            model_id=model_id,
                                            parameters=parameters, metrics=metrics)


def compare_experiment_runs(experiment_id):
    """Compare experiment runs."""
    return _get_client().compare_experiment_runs(experiment_id)


# ─── Hyperparameters ────────────────────────────────────────────────


def create_hyperparameters(name, parameters, model_id=None, description=None):
    """Create a hyperparameter set."""
    return _get_client().create_hyperparameters(name, parameters, model_id=model_id,
                                                description=description)


def load_hyperparameters(name_or_id):
    """Load hyperparameter set."""
    return _get_client().load_hyperparameters(name_or_id)


# ─── Pipelines ──────────────────────────────────────────────────────


def create_pipeline(name, steps, description=None):
    """Create a pipeline."""
    return _get_client().create_pipeline(name, steps, description=description)


def run_pipeline(pipeline_id, wait=False):
    """Run a pipeline."""
    return _get_client().run_pipeline(pipeline_id, wait=wait)


# ─── Data Query Methods ──────────────────────────────────────────────


def query_spark(query, spark_master=None):
    """Execute a Spark SQL query and return results."""
    return _get_client().query_spark(query, spark_master=spark_master)


def query_elasticsearch(index, query_body, es_host=None):
    """Execute an Elasticsearch query and return hits."""
    return _get_client().query_elasticsearch(index, query_body, es_host=es_host)


# ─── UBA-Specific Query Methods ─────────────────────────────────────


def query_anomalies(entity_id=None, model_id=None, min_risk=None,
                    max_risk=None, limit=1000):
    """Query anomalies from the platform."""
    return _get_client().query_anomalies(entity_id=entity_id, model_id=model_id,
                                         min_risk=min_risk, max_risk=max_risk,
                                         limit=limit)


def get_entity_risk(entity_id):
    """Get entity risk profile."""
    return _get_client().get_entity_risk(entity_id)


def query_cases(status=None, severity=None, limit=100):
    """Query security cases."""
    return _get_client().query_cases(status=status, severity=severity, limit=limit)


def list_rules(enabled=True):
    """List detection rules."""
    return _get_client().list_rules(enabled=enabled)


__all__ = [
    # Core classes
    "OpenUBAClient",
    "VisualizationContext",
    "ModelContext",
    # Configuration
    "configure",
    # Original model management
    "install",
    "uninstall",
    "run",
    "list_models",
    "list_installed",
    "get_model",
    # Model registration
    "register_model",
    "publish_version",
    "load_model",
    # Datasets
    "list_datasets",
    "get_dataset",
    "create_dataset",
    # Jobs
    "start_training",
    "start_inference",
    "get_job",
    "wait_for_job",
    "get_logs",
    "post_log",
    # Visualizations
    "create_visualization",
    "update_visualization",
    "publish_visualization",
    "list_visualizations",
    "render",
    # Dashboards
    "create_dashboard",
    "update_dashboard",
    "list_dashboards",
    # Features
    "create_features",
    "load_features",
    # Experiments
    "create_experiment",
    "add_experiment_run",
    "compare_experiment_runs",
    # Hyperparameters
    "create_hyperparameters",
    "load_hyperparameters",
    # Pipelines
    "create_pipeline",
    "run_pipeline",
    # Data queries
    "query_spark",
    "query_elasticsearch",
    # UBA queries
    "query_anomalies",
    "get_entity_risk",
    "query_cases",
    "list_rules",
]
