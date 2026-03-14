"""OpenUBA client — fetches and installs models from the openuba-model-hub registry."""

import hashlib
import importlib.util
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml


# ── Registry defaults ────────────────────────────────────────────────
DEFAULT_REGISTRY_URL = "https://openuba.org/registry/models.json"
DEFAULT_RAW_BASE_URL = (
    "https://raw.githubusercontent.com/GACWR/openuba-model-hub/master"
)
MODEL_FILES = ["MODEL.py", "model.yaml", "__init__.py"]
CACHE_TTL_SECONDS = 300


def _default_model_dir() -> Path:
    """Return the default directory for installed models."""
    return Path(os.environ.get("OPENUBA_MODEL_DIR", Path.home() / ".openuba" / "models"))


class OpenUBAClient:
    """Fetch model catalog from the openuba-model-hub registry and install
    model code locally.  Works fully offline-capable after first install."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        token: Optional[str] = None,
        registry_url: Optional[str] = None,
        model_dir: Optional[str] = None,
    ):
        # Server API (used for run when a server is available)
        self.api_url = (
            api_url or os.environ.get("OPENUBA_API_URL") or "http://localhost:8000"
        ).rstrip("/")
        self.token = token or os.environ.get("OPENUBA_TOKEN")
        self.workspace_id = os.environ.get("OPENUBA_WORKSPACE_ID")

        # Hub registry (used for list/install — works without a server)
        self.registry_url = (
            registry_url
            or os.environ.get("OPENUBA_HUB_URL")
            or DEFAULT_REGISTRY_URL
        )
        self.raw_base_url = os.environ.get(
            "OPENUBA_HUB_RAW_BASE_URL", DEFAULT_RAW_BASE_URL
        )
        self.model_dir = Path(model_dir) if model_dir else _default_model_dir()

        self._session = requests.Session()
        if self.token:
            self._session.headers["Authorization"] = f"Bearer {self.token}"

        # In-memory registry cache
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0

    # ── Registry helpers ─────────────────────────────────────────────

    def _fetch_registry(self) -> Dict[str, Any]:
        """Fetch and cache the model hub registry JSON."""
        now = time.time()
        if self._cache and (now - self._cache_time) < CACHE_TTL_SECONDS:
            return self._cache

        resp = self._session.get(self.registry_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self._cache = data
        self._cache_time = now
        return data

    def _find_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Find a model entry by name or slug."""
        registry = self._fetch_registry()
        for model in registry.get("models", []):
            if model.get("name") == model_id or model.get("slug") == model_id:
                return model
        return None

    # ── Public API ───────────────────────────────────────────────────

    def list_models(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """List models available in the openuba-model-hub registry."""
        registry = self._fetch_registry()
        models = registry.get("models", [])
        if source:
            models = [m for m in models if m.get("runtime") == source]
        return models

    def get_model(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for a specific model from the registry."""
        model = self._find_model(model_name)
        if not model:
            raise ValueError(f"Model not found in registry: {model_name}")
        # Enrich with local install status
        install_path = self.model_dir / model["name"]
        model["installed"] = install_path.exists()
        model["install_path"] = str(install_path)
        return model

    def install_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download model files from the hub and install locally.

        Downloads MODEL.py, model.yaml, and __init__.py from the
        openuba-model-hub GitHub repo into ~/.openuba/models/<model_name>/.
        """
        model = self._find_model(model_name)
        if not model:
            raise ValueError(f"Model not found in registry: {model_name}")

        if version and model.get("version") != version:
            raise ValueError(
                f"Requested version {version} but registry has {model.get('version')}"
            )

        model_path = model.get("path")
        if not model_path:
            raise ValueError(f"Model {model_name} has no path in registry")

        dest = self.model_dir / model["name"]
        dest.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        for filename in MODEL_FILES:
            url = f"{self.raw_base_url}/{model_path}/{filename}"
            try:
                resp = self._session.get(url, timeout=15)
                if resp.status_code == 200:
                    file_path = dest / filename
                    file_path.write_bytes(resp.content)
                    downloaded += 1
                # 404 is expected for optional files like __init__.py
            except requests.RequestException:
                pass

        if downloaded == 0:
            raise RuntimeError(f"No files could be downloaded for {model_name}")

        # Write an install manifest so we can track what's installed
        manifest = {
            "name": model["name"],
            "version": model.get("version"),
            "runtime": model.get("runtime"),
            "framework": model.get("framework"),
            "description": model.get("description"),
            "installed_from": "openuba_hub",
            "files": [f for f in MODEL_FILES if (dest / f).exists()],
            "file_hashes": {
                f: _hash_file(dest / f)
                for f in MODEL_FILES
                if (dest / f).exists()
            },
        }
        manifest_path = dest / "manifest.json"
        import json
        manifest_path.write_text(json.dumps(manifest, indent=2))

        return {
            "name": model["name"],
            "version": model.get("version"),
            "runtime": model.get("runtime"),
            "path": str(dest),
            "files_downloaded": downloaded,
            "status": "installed",
        }

    def uninstall_model(self, model_name: str) -> Dict[str, Any]:
        """Remove a locally installed model."""
        dest = self.model_dir / model_name
        if not dest.exists():
            raise ValueError(f"Model {model_name} is not installed")
        shutil.rmtree(dest)
        return {"name": model_name, "status": "uninstalled"}

    def list_installed(self) -> List[Dict[str, Any]]:
        """List locally installed models."""
        if not self.model_dir.exists():
            return []
        installed = []
        for item in sorted(self.model_dir.iterdir()):
            if not item.is_dir():
                continue
            info: Dict[str, Any] = {"name": item.name, "path": str(item)}
            yaml_path = item / "model.yaml"
            if yaml_path.exists():
                try:
                    meta = yaml.safe_load(yaml_path.read_text())
                    info.update({
                        "version": meta.get("version"),
                        "runtime": meta.get("runtime"),
                        "description": meta.get("description"),
                    })
                except Exception:
                    pass
            installed.append(info)
        return installed

    def run_model(
        self,
        model_name: str,
        data: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run an installed model locally.

        Loads the model's MODEL.py, instantiates the Model class, and
        calls its train/infer methods with a lightweight context.
        """
        model_dir = self.model_dir / model_name
        if not model_dir.exists():
            raise ValueError(
                f"Model {model_name} is not installed. Run: openuba install {model_name}"
            )

        model_py = model_dir / "MODEL.py"
        if not model_py.exists():
            raise ValueError(f"MODEL.py not found in {model_dir}")

        # Load the model module dynamically
        spec = importlib.util.spec_from_file_location(
            f"openuba.models.{model_name}", str(model_py)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "Model"):
            raise ValueError(f"MODEL.py in {model_name} has no Model class")

        model_instance = mod.Model()

        # Build a lightweight execution context
        ctx = _ModelContext(
            model_name=model_name,
            data_path=data,
            parameters=parameters or {},
        )

        # Run inference (or train+infer if model supports it)
        if hasattr(model_instance, "infer"):
            result = model_instance.infer(ctx)
        elif hasattr(model_instance, "execute"):
            result = model_instance.execute(ctx.df)
        else:
            raise ValueError(f"Model {model_name} has no infer() or execute() method")

        # Convert result to serializable dict
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            return {"status": "success", "results": result.to_dict("records")}
        if isinstance(result, dict):
            return {"status": "success", **result}
        return {"status": "success", "results": result}

    # ─── HTTP helpers ───────────────────────────────────────────────

    def _headers(self):
        '''get request headers with auth token'''
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, path, params=None):
        '''authenticated GET request'''
        url = f"{self.api_url}{path}"
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, path, body=None):
        '''authenticated POST request'''
        url = f"{self.api_url}{path}"
        response = requests.post(url, headers=self._headers(), json=body)
        response.raise_for_status()
        return response.json()

    def _put(self, path, body=None):
        '''authenticated PUT request'''
        url = f"{self.api_url}{path}"
        response = requests.put(url, headers=self._headers(), json=body)
        response.raise_for_status()
        return response.json()

    def _patch(self, path, body=None):
        '''authenticated PATCH request'''
        url = f"{self.api_url}{path}"
        response = requests.patch(url, headers=self._headers(), json=body)
        response.raise_for_status()
        return response.json()

    def _delete(self, path):
        '''authenticated DELETE request'''
        url = f"{self.api_url}{path}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
        return True

    # ─── Model Registration (SDK-first) ─────────────────────────────

    def register_model(self, name, model=None, framework=None, description=None):
        '''register a model with the platform, optionally with auto-detection'''
        body = {"name": name, "description": description or ""}
        if model is not None:
            detected = framework or self._detect_framework(model)
            body["framework"] = detected
            serialized = self._serialize_model(model, detected)
            body["model_data"] = serialized
        elif framework:
            body["framework"] = framework
        return self._post("/api/v1/sdk/register-model", body)

    def publish_version(self, model_id, version=None, summary=None):
        '''publish a new version of a model'''
        body = {"model_id": str(model_id)}
        if version:
            body["version"] = version
        if summary:
            body["summary"] = summary
        return self._post("/api/v1/sdk/publish-version", body)

    def load_model(self, name_or_id, version=None):
        '''load a model by name or ID'''
        try:
            return self._get(f"/api/v1/sdk/models/resolve/{name_or_id}")
        except Exception:
            return self._get(f"/api/v1/models/{name_or_id}")

    # ─── Dataset Management ─────────────────────────────────────────

    def list_datasets(self):
        '''list all datasets'''
        return self._get("/api/v1/datasets")

    def get_dataset(self, dataset_id):
        '''get dataset by ID'''
        return self._get(f"/api/v1/datasets/{dataset_id}")

    def create_dataset(self, name, description=None, source_type="upload", format="csv"):
        '''create a dataset record'''
        return self._post("/api/v1/datasets", {
            "name": name,
            "description": description,
            "source_type": source_type,
            "format": format,
        })

    # ─── Jobs ───────────────────────────────────────────────────────

    def start_training(self, model_id, dataset_id=None, hardware_tier="cpu-small",
                       hyperparameters=None, wait=False):
        '''start a training job'''
        body = {
            "model_id": str(model_id),
            "job_type": "training",
            "hardware_tier": hardware_tier,
        }
        if dataset_id:
            body["dataset_id"] = str(dataset_id)
        if hyperparameters:
            body["hyperparameters"] = hyperparameters
        result = self._post("/api/v1/jobs", body)
        if wait and result.get("id"):
            return self.wait_for_job(result["id"])
        return result

    def start_inference(self, model_id, dataset_id=None, hardware_tier="cpu-small",
                        wait=False):
        '''start an inference job'''
        body = {
            "model_id": str(model_id),
            "job_type": "inference",
            "hardware_tier": hardware_tier,
        }
        if dataset_id:
            body["dataset_id"] = str(dataset_id)
        result = self._post("/api/v1/jobs", body)
        if wait and result.get("id"):
            return self.wait_for_job(result["id"])
        return result

    def get_job(self, job_id):
        '''get job details'''
        return self._get(f"/api/v1/jobs/{job_id}")

    def wait_for_job(self, job_id, poll_interval=2, timeout=3600):
        '''wait for a job to complete'''
        import time as _time
        start = _time.time()
        while _time.time() - start < timeout:
            job = self.get_job(job_id)
            status = job.get("status", "unknown")
            if status in ("completed", "failed", "error"):
                return job
            _time.sleep(poll_interval)
        raise TimeoutError(f"job {job_id} did not complete within {timeout}s")

    def get_logs(self, job_id):
        '''get job logs'''
        return self._get(f"/api/v1/jobs/{job_id}/logs")

    def post_log(self, job_id, message, level="info"):
        '''post a log entry for a job'''
        return self._post(f"/api/v1/internal/logs/{job_id}", {
            "message": message,
            "level": level,
        })

    # ─── Visualizations ─────────────────────────────────────────────

    def create_visualization(self, name, backend="matplotlib", description=None,
                              output_type=None):
        '''create a visualization'''
        if output_type is None:
            output_type_map = {
                "matplotlib": "svg", "seaborn": "svg", "plotly": "plotly",
                "bokeh": "bokeh", "altair": "vega-lite", "plotnine": "svg",
                "datashader": "png", "networkx": "svg", "geopandas": "svg",
            }
            output_type = output_type_map.get(backend, "svg")
        return self._post("/api/v1/visualizations", {
            "name": name,
            "backend": backend,
            "output_type": output_type,
            "description": description,
        })

    def publish_visualization(self, viz_id):
        '''publish a visualization'''
        return self._post(f"/api/v1/visualizations/{viz_id}/publish")

    def list_visualizations(self):
        '''list all visualizations'''
        return self._get("/api/v1/visualizations")

    # ─── Dashboards ─────────────────────────────────────────────────

    def create_dashboard(self, name, layout=None, description=None):
        '''create a dashboard'''
        return self._post("/api/v1/dashboards", {
            "name": name,
            "layout": layout or [],
            "description": description,
        })

    def update_dashboard(self, dashboard_id, layout=None, name=None):
        '''update a dashboard'''
        body = {}
        if layout is not None:
            body["layout"] = layout
        if name is not None:
            body["name"] = name
        return self._put(f"/api/v1/dashboards/{dashboard_id}", body)

    def list_dashboards(self):
        '''list all dashboards'''
        return self._get("/api/v1/dashboards")

    # ─── Features ───────────────────────────────────────────────────

    def create_features(self, feature_names, group_name, description=None, entity="default"):
        '''create a feature group with features'''
        group = self._post("/api/v1/features/groups", {
            "name": group_name,
            "description": description,
            "entity": entity,
        })
        group_id = group.get("id")
        for fname in feature_names:
            self._post(f"/api/v1/features/groups/{group_id}/features", {
                "group_id": group_id,
                "name": fname,
            })
        return group

    def load_features(self, group_name):
        '''load feature group by name'''
        return self._get(f"/api/v1/features/groups/name/{group_name}")

    # ─── Experiments ────────────────────────────────────────────────

    def create_experiment(self, name, description=None):
        '''create an experiment'''
        return self._post("/api/v1/experiments", {
            "name": name,
            "description": description,
        })

    def add_experiment_run(self, experiment_id, job_id=None, model_id=None,
                           parameters=None, metrics=None):
        '''add a run to an experiment'''
        body = {}
        if job_id:
            body["job_id"] = str(job_id)
        if model_id:
            body["model_id"] = str(model_id)
        if parameters:
            body["parameters"] = parameters
        if metrics:
            body["metrics"] = metrics
        return self._post(f"/api/v1/experiments/{experiment_id}/runs", body)

    def compare_experiment_runs(self, experiment_id):
        '''compare experiment runs'''
        return self._get(f"/api/v1/experiments/{experiment_id}/compare")

    # ─── Hyperparameters ────────────────────────────────────────────

    def create_hyperparameters(self, name, parameters, model_id=None, description=None):
        '''create a hyperparameter set'''
        body = {"name": name, "parameters": parameters}
        if model_id:
            body["model_id"] = str(model_id)
        if description:
            body["description"] = description
        return self._post("/api/v1/hyperparameters", body)

    def load_hyperparameters(self, name_or_id):
        '''load hyperparameter set'''
        return self._get(f"/api/v1/hyperparameters/{name_or_id}")

    # ─── Pipelines ──────────────────────────────────────────────────

    def create_pipeline(self, name, steps, description=None):
        '''create a pipeline'''
        return self._post("/api/v1/pipelines", {
            "name": name,
            "steps": steps,
            "description": description,
        })

    def run_pipeline(self, pipeline_id, wait=False):
        '''run a pipeline'''
        result = self._post(f"/api/v1/pipelines/{pipeline_id}/run")
        return result

    # ─── UBA-Specific Query Methods ─────────────────────────────────

    def query_anomalies(self, entity_id=None, model_id=None, min_risk=None,
                        max_risk=None, limit=1000):
        '''query anomalies from the platform'''
        params = {"limit": limit}
        if entity_id:
            params["entity_id"] = entity_id
        if model_id:
            params["model_id"] = str(model_id)
        if min_risk is not None:
            params["min_risk_score"] = min_risk
        if max_risk is not None:
            params["max_risk_score"] = max_risk
        return self._get("/api/v1/anomalies", params=params)

    def get_entity_risk(self, entity_id):
        '''get entity risk profile'''
        return self._get(f"/api/v1/entities/{entity_id}")

    def query_cases(self, status=None, severity=None, limit=100):
        '''query security cases'''
        params = {"limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        return self._get("/api/v1/cases", params=params)

    def list_rules(self, enabled=True):
        '''list detection rules'''
        return self._get("/api/v1/rules", params={"enabled": enabled})

    # ─── Data Query Methods ─────────────────────────────────────────

    def query_spark(self, query, spark_master=None):
        '''execute a Spark SQL query and return results as list of dicts'''
        try:
            from pyspark.sql import SparkSession
        except ImportError:
            raise ImportError("pyspark is required for query_spark(). Install with: pip install pyspark")

        master = spark_master or os.environ.get("SPARK_MASTER", "local[*]")
        spark = SparkSession.builder \
            .appName("openuba-sdk") \
            .master(master) \
            .getOrCreate()

        df = spark.sql(query)
        results = [row.asDict() for row in df.collect()]
        return results

    def query_elasticsearch(self, index, query_body, es_host=None):
        '''execute an Elasticsearch query and return hits'''
        try:
            from elasticsearch import Elasticsearch
        except ImportError:
            raise ImportError("elasticsearch is required for query_elasticsearch(). Install with: pip install elasticsearch")

        host = es_host or os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
        es = Elasticsearch(host)
        result = es.search(index=index, body=query_body)
        hits = result.get("hits", {}).get("hits", [])
        return [hit.get("_source", {}) for hit in hits]

    # ─── Source Code Generation ────────────────────────────────────

    def _generate_source_code(self, model_name, framework=None, template="basic"):
        '''generate boilerplate MODEL.py source code for a given framework'''
        fw = framework or "sklearn"
        templates = {
            "sklearn": _SKLEARN_TEMPLATE,
            "pytorch": _PYTORCH_TEMPLATE,
            "tensorflow": _TENSORFLOW_TEMPLATE,
        }
        code = templates.get(fw, _SKLEARN_TEMPLATE)
        return code.replace("{{MODEL_NAME}}", model_name)

    # ─── Framework Detection ────────────────────────────────────────

    @staticmethod
    def _detect_framework(model):
        '''detect ML framework from model object'''
        module = type(model).__module__
        if 'sklearn' in module:
            return 'sklearn'
        elif 'torch' in module:
            return 'pytorch'
        elif 'tensorflow' in module or 'keras' in module:
            return 'tensorflow'
        elif 'networkx' in module:
            return 'networkx'
        return 'unknown'

    @staticmethod
    def _serialize_model(model, framework):
        '''serialize model to base64 string'''
        import base64
        import pickle
        import io
        buf = io.BytesIO()
        if framework == 'sklearn':
            pickle.dump(model, buf)
        elif framework == 'pytorch':
            import torch
            torch.save(model, buf)
        elif framework == 'tensorflow':
            pickle.dump(model, buf)
        else:
            pickle.dump(model, buf)
        return base64.b64encode(buf.getvalue()).decode('utf-8')


class _ModelContext:
    """Lightweight model execution context for running models locally."""

    def __init__(self, model_name: str, data_path: Optional[str], parameters: dict):
        self.model_name = model_name
        self.parameters = parameters
        self.df = None
        self.logger = _SimpleLogger(model_name)

        if data_path:
            import pandas as pd
            if data_path.endswith(".csv"):
                self.df = pd.read_csv(data_path)
            elif data_path.endswith(".parquet"):
                self.df = pd.read_parquet(data_path)
            elif data_path.endswith(".json"):
                self.df = pd.read_json(data_path)
            else:
                self.df = pd.read_csv(data_path)

    def log_metric(self, name: str, value: float, **kwargs):
        self.logger.info(f"metric {name}={value}")


class _SimpleLogger:
    """Minimal logger that prints to stdout for local model execution."""

    def __init__(self, name: str):
        self._name = name

    def info(self, msg: str):
        print(f"[{self._name}] {msg}")

    def warning(self, msg: str):
        print(f"[{self._name}] WARNING: {msg}")

    def error(self, msg: str):
        print(f"[{self._name}] ERROR: {msg}")


_SKLEARN_TEMPLATE = '''"""{{MODEL_NAME}} — sklearn-based UBA model."""

import pandas as pd
from sklearn.ensemble import IsolationForest


class Model:
    def __init__(self):
        self.clf = IsolationForest(contamination=0.05, random_state=42)

    def train(self, ctx):
        self.clf.fit(ctx.df)
        ctx.logger.info("training complete")
        return {"status": "trained"}

    def infer(self, ctx):
        predictions = self.clf.predict(ctx.df)
        ctx.df["anomaly_score"] = self.clf.score_samples(ctx.df)
        ctx.df["is_anomaly"] = predictions == -1
        return ctx.df
'''

_PYTORCH_TEMPLATE = '''"""{{MODEL_NAME}} — PyTorch-based UBA model."""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np


class Autoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(hidden_dim, input_dim), nn.Sigmoid())

    def forward(self, x):
        return self.decoder(self.encoder(x))


class Model:
    def __init__(self):
        self.model = None
        self.threshold = None

    def train(self, ctx):
        data = torch.FloatTensor(ctx.df.values)
        self.model = Autoencoder(data.shape[1])
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()

        for epoch in range(50):
            output = self.model(data)
            loss = criterion(output, data)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            ctx.log_metric("loss", loss.item(), epoch=epoch)

        with torch.no_grad():
            recon = self.model(data)
            errors = ((recon - data) ** 2).mean(dim=1).numpy()
            self.threshold = np.percentile(errors, 95)

        ctx.logger.info(f"training complete, threshold={self.threshold:.4f}")
        return {"status": "trained", "threshold": self.threshold}

    def infer(self, ctx):
        data = torch.FloatTensor(ctx.df.values)
        with torch.no_grad():
            recon = self.model(data)
            errors = ((recon - data) ** 2).mean(dim=1).numpy()
        ctx.df["reconstruction_error"] = errors
        ctx.df["is_anomaly"] = errors > self.threshold
        return ctx.df
'''

_TENSORFLOW_TEMPLATE = '''"""{{MODEL_NAME}} — TensorFlow/Keras-based UBA model."""

import numpy as np
import pandas as pd


class Model:
    def __init__(self):
        self.model = None
        self.threshold = None

    def train(self, ctx):
        import tensorflow as tf

        data = ctx.df.values.astype("float32")
        input_dim = data.shape[1]

        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation="relu", input_shape=(input_dim,)),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(input_dim, activation="sigmoid"),
        ])
        self.model.compile(optimizer="adam", loss="mse")
        self.model.fit(data, data, epochs=50, batch_size=32, verbose=0)

        recon = self.model.predict(data)
        errors = np.mean((recon - data) ** 2, axis=1)
        self.threshold = np.percentile(errors, 95)

        ctx.logger.info(f"training complete, threshold={self.threshold:.4f}")
        return {"status": "trained"}

    def infer(self, ctx):
        data = ctx.df.values.astype("float32")
        recon = self.model.predict(data)
        errors = np.mean((recon - data) ** 2, axis=1)
        ctx.df["reconstruction_error"] = errors
        ctx.df["is_anomaly"] = errors > self.threshold
        return ctx.df
'''


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
