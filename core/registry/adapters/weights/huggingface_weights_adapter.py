'''
Copyright 2019-Present The OpenUBA Platform Authors
hugging face hub weights adapter
'''

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from core.registry.base_weights_adapter import BaseWeightsAdapter

logger = logging.getLogger(__name__)


class HuggingFaceWeightsAdapter(BaseWeightsAdapter):
    '''
    adapter for hugging face model hub (weights registry)
    '''

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        self.api_base = "https://huggingface.co/api"

    def _get_headers(self) -> Dict[str, str]:
        '''
        get request headers with auth if token available
        '''
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def list_weights(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        search hugging face for model weights tagged with openuba
        '''
        try:
            url = f"{self.api_base}/models"
            params = {"search": "openuba"}
            if model_name:
                params["search"] = f"openuba {model_name}"
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            weights = []
            for model in data:
                # try to get weights manifest
                try:
                    manifest = self._get_manifest_from_model(model["id"])
                    if manifest:
                        weights.append(manifest)
                except Exception:
                    pass
            return weights
        except Exception as e:
            logger.error(f"error listing weights from huggingface: {e}")
            return []

    def _get_manifest_from_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        '''
        get weights manifest from huggingface model
        '''
        try:
            url = f"{self.api_base}/models/{model_id}"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            manifest = {
                "weights_id": model_id,
                "model_name": data.get("id", "").split("/")[-1],
                "version": data.get("sha", "latest"),
                "format": "pytorch",  # default, could be detected
                "source_url": f"https://huggingface.co/{model_id}"
            }
            return self.normalize_weights_manifest(manifest)
        except Exception as e:
            logger.debug(f"error getting manifest for {model_id}: {e}")
            return None

    def fetch_weights(self, weights_id: str) -> Dict[str, Any]:
        '''
        fetch weights from huggingface
        '''
        manifest = self._get_manifest_from_model(weights_id)
        if not manifest:
            raise ValueError(f"weights not found: {weights_id}")
        return manifest

    def download_weights(self, weights_id: str, destination: str) -> str:
        '''
        download weights from huggingface using huggingface_hub library if available
        '''
        try:
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(
                    repo_id=weights_id,
                    local_dir=destination,
                    token=self.token
                )
                logger.info(f"downloaded weights {weights_id} to {destination}")
                return destination
            except ImportError:
                logger.warning("huggingface_hub not installed, using git clone fallback")
                import subprocess
                repo_url = f"https://huggingface.co/{weights_id}"
                subprocess.run(
                    ["git", "clone", repo_url, destination],
                    check=True,
                    capture_output=True
                )
                return destination
        except Exception as e:
            logger.error(f"error downloading weights from huggingface: {e}")
            raise

    def get_source_type(self) -> str:
        return "huggingface"

