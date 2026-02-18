'''
Copyright 2019-Present The OpenUBA Platform Authors
hugging face hub adapter
'''

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)


class HuggingFaceAdapter(BaseRegistryAdapter):
    '''
    adapter for hugging face model hub
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

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        search hugging face for models tagged with openuba
        '''
        try:
            url = f"{self.api_base}/models"
            params = {"search": "openuba"}
            if query:
                params["search"] = f"openuba {query}"
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            models = []
            for model in data:
                # try to get model manifest
                try:
                    manifest = self._get_manifest_from_model(model["id"])
                    if manifest:
                        models.append(manifest)
                except Exception:
                    pass
            return models
        except Exception as e:
            logger.error(f"error listing models from huggingface: {e}")
            return []

    def _get_manifest_from_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        '''
        get model manifest from huggingface model
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
                "name": data.get("id", "").split("/")[-1],
                "version": data.get("sha", "latest"),
                "author": data.get("author", ""),
                "description": data.get("description", ""),
                "source_url": f"https://huggingface.co/{model_id}",
                "framework": "pytorch"  # default, could be detected
            }
            return self.normalize_manifest(manifest)
        except Exception as e:
            logger.debug(f"error getting manifest for {model_id}: {e}")
            return None

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch model from huggingface
        '''
        manifest = self._get_manifest_from_model(model_id)
        if not manifest:
            raise ValueError(f"model not found: {model_id}")
        return manifest

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        download model from huggingface using huggingface_hub library if available
        '''
        try:
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(
                    repo_id=model_id,
                    local_dir=destination,
                    token=self.token
                )
                logger.info(f"downloaded model {model_id} to {destination}")
                return destination
            except ImportError:
                logger.warning("huggingface_hub not installed, using git clone fallback")
                import subprocess
                repo_url = f"https://huggingface.co/{model_id}"
                subprocess.run(
                    ["git", "clone", repo_url, destination],
                    check=True,
                    capture_output=True
                )
                return destination
        except Exception as e:
            logger.error(f"error downloading model from huggingface: {e}")
            raise

    def get_source_type(self) -> str:
        return "huggingface"

