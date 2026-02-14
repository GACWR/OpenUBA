'''
Copyright 2019-Present The OpenUBA Platform Authors
kubeflow model registry weights adapter
'''

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from core.registry.base_weights_adapter import BaseWeightsAdapter

logger = logging.getLogger(__name__)


class KubeflowWeightsAdapter(BaseWeightsAdapter):
    '''
    adapter for kubeflow model registry (weights)
    '''

    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url or os.getenv(
            "KUBEFLOW_REGISTRY_URL",
            "http://localhost:8080"
        )

    def list_weights(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list weights from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models"
            params = {}
            if model_name:
                params["filter"] = model_name
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            weights = []
            for model in data.get("models", []):
                weights.append(self.normalize_weights_manifest(model))
            return weights
        except Exception as e:
            logger.error(f"error listing weights from kubeflow: {e}")
            return []

    def fetch_weights(self, weights_id: str) -> Dict[str, Any]:
        '''
        fetch weights from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models/{weights_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self.normalize_weights_manifest(data)
        except Exception as e:
            logger.error(f"error fetching weights {weights_id}: {e}")
            raise

    def download_weights(self, weights_id: str, destination: str) -> str:
        '''
        download weights from kubeflow registry
        '''
        try:
            url = f"{self.registry_url}/api/v1/models/{weights_id}/download"
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
            logger.info(f"downloaded weights {weights_id} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"error downloading weights from kubeflow: {e}")
            raise

    def get_source_type(self) -> str:
        return "kubeflow"

