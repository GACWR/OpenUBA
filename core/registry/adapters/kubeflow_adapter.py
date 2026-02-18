'''
Copyright 2019-Present The OpenUBA Platform Authors
kubeflow model registry adapter
'''

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)


class KubeflowAdapter(BaseRegistryAdapter):
    '''
    adapter for kubeflow model registry
    '''

    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url or os.getenv(
            "KUBEFLOW_REGISTRY_URL",
            "http://localhost:8080"
        )

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list models from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models"
            params = {}
            if query:
                params["filter"] = query
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append(self.normalize_manifest(model))
            return models
        except Exception as e:
            logger.error(f"error listing models from kubeflow: {e}")
            return []

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch model from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models/{model_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self.normalize_manifest(data)
        except Exception as e:
            logger.error(f"error fetching model {model_id}: {e}")
            raise

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        download model from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models/{model_id}/download"
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            import zipfile
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            with zipfile.ZipFile(tmp_path, "r") as zip_ref:
                zip_ref.extractall(destination)
            os.unlink(tmp_path)
            logger.info(f"downloaded model {model_id} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"error downloading model from kubeflow: {e}")
            raise

    def get_source_type(self) -> str:
        return "kubeflow"

