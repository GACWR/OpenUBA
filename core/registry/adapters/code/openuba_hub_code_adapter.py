'''
Copyright 2019-Present The OpenUBA Platform Authors
openuba hub code registry adapter
fetches model catalog from the openuba-model-hub registry (GitHub raw or deployed site)
'''

import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)

# default: official openuba.org registry endpoint
DEFAULT_REGISTRY_URL = (
    "https://openuba.org/registry/models.json"
)
# base URL for downloading raw model files from the repo
DEFAULT_RAW_BASE_URL = (
    "https://raw.githubusercontent.com/GACWR/openuba-model-hub/master"
)
# files to download for each model
MODEL_FILES = ["MODEL.py", "model.yaml", "__init__.py"]

CACHE_TTL_SECONDS = int(os.getenv("HUB_CACHE_TTL_SECONDS", "300"))


class OpenUBAHubCodeAdapter(BaseRegistryAdapter):
    '''
    adapter for the official openuba model hub (code registry)
    fetches the catalog from a static JSON endpoint and downloads
    model files from GitHub raw URLs
    '''

    def __init__(self, hub_url: Optional[str] = None):
        self.registry_url = hub_url or os.getenv("OPENUBA_HUB_URL", DEFAULT_REGISTRY_URL)
        self.raw_base_url = os.getenv("OPENUBA_HUB_RAW_BASE_URL", DEFAULT_RAW_BASE_URL)
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0

    def _fetch_registry(self) -> Dict[str, Any]:
        '''
        fetch and cache the full registry JSON
        '''
        now = time.time()
        if self._cache and (now - self._cache_time) < CACHE_TTL_SECONDS:
            return self._cache

        try:
            response = requests.get(self.registry_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            self._cache = data
            self._cache_time = now
            logger.info(f"fetched hub registry: {len(data.get('models', []))} models")
            return data
        except Exception as e:
            logger.error(f"error fetching hub registry from {self.registry_url}: {e}")
            if self._cache:
                logger.warning("using stale cache")
                return self._cache
            return {"models": []}

    def _find_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        '''
        find a model by name or slug in the registry
        '''
        registry = self._fetch_registry()
        for model in registry.get("models", []):
            if model.get("name") == model_id or model.get("slug") == model_id:
                return model
        return None

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list available models from the openuba hub
        fetches full catalog and filters client-side
        '''
        registry = self._fetch_registry()
        models = registry.get("models", [])

        if query:
            q = query.lower()
            models = [
                m for m in models
                if q in m.get("name", "").lower()
                or q in m.get("description", "").lower()
                or q in m.get("framework", "").lower()
                or any(q in tag.lower() for tag in m.get("tags", []))
            ]

        return [self.normalize_manifest(m) for m in models]

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch a specific model's metadata from the hub
        '''
        model = self._find_model(model_id)
        if not model:
            raise ValueError(f"model not found in hub: {model_id}")
        return self.normalize_manifest(model)

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        '''
        get model manifest (alias for fetch_model)
        '''
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        download model files from the hub's GitHub repository
        '''
        model = self._find_model(model_id)
        if not model:
            raise ValueError(f"model not found in hub: {model_id}")

        model_path = model.get("path")
        if not model_path:
            raise ValueError(f"model {model_id} has no path field in registry")

        os.makedirs(destination, exist_ok=True)

        downloaded = 0
        for filename in MODEL_FILES:
            url = f"{self.raw_base_url}/{model_path}/{filename}"
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    file_path = os.path.join(destination, filename)
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    downloaded += 1
                    logger.info(f"downloaded {filename} for {model_id}")
                elif response.status_code == 404:
                    logger.debug(f"{filename} not found for {model_id}, skipping")
                else:
                    logger.warning(f"unexpected status {response.status_code} fetching {url}")
            except Exception as e:
                logger.warning(f"error downloading {filename} for {model_id}: {e}")

        if downloaded == 0:
            raise ValueError(f"no files downloaded for model {model_id}")

        logger.info(f"downloaded {downloaded} files for {model_id} to {destination}")
        return destination

    def normalize_manifest(self, raw_manifest: Dict[str, Any]) -> Dict[str, Any]:
        '''
        normalize hub manifest, preserving all hub-specific fields
        '''
        name = raw_manifest.get("name", "")
        return {
            "name": name,
            "slug": raw_manifest.get("slug"),
            "version": raw_manifest.get("version"),
            "author": raw_manifest.get("author"),
            "description": raw_manifest.get("description"),
            "framework": raw_manifest.get("framework"),
            "runtime": raw_manifest.get("runtime"),
            "tags": raw_manifest.get("tags", []),
            "parameters": raw_manifest.get("parameters", []),
            "license": raw_manifest.get("license"),
            "path": raw_manifest.get("path"),
            "dependencies": raw_manifest.get("dependencies", []),
            "components": raw_manifest.get("components", []),
            "source_type": self.get_source_type(),
            "source_url": f"https://github.com/GACWR/openuba-model-hub/tree/master/{raw_manifest.get('path', '')}",
        }

    def get_source_type(self) -> str:
        return "openuba_hub"
