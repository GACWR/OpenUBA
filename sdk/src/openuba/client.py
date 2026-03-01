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


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
