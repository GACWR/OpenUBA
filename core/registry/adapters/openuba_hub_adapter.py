'''
Copyright 2019-Present The OpenUBA Platform Authors
openuba hub registry adapter
'''

import os
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)


class OpenUBAHubAdapter(BaseRegistryAdapter):
    '''
    adapter for openuba default model hub
    '''

    def __init__(self, hub_url: Optional[str] = None):
        self.hub_url = hub_url or os.getenv(
            "OPENUBA_HUB_URL",
            "http://openuba.gacwr.org"
        )

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list available models from openuba hub
        '''
        try:
            url = f"{self.hub_url}/ml/"
            if query:
                url += f"?q={query}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            # normalize response format
            models = data.get("models", [])
            return [self.normalize_manifest(m) for m in models]
        except Exception as e:
            logger.error(f"error listing models from openuba hub: {e}")
            return []

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch model metadata from hub
        '''
        try:
            url = f"{self.hub_url}/ml/{model_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self.normalize_manifest(data)
        except Exception as e:
            logger.error(f"error fetching model {model_id}: {e}")
            raise

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        '''
        get model manifest
        '''
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        download model files from hub
        '''
        import shutil
        import tempfile
        try:
            # get model metadata
            manifest = self.get_manifest(model_id)
            # create destination directory
            os.makedirs(destination, exist_ok=True)
            # download model files - TODO
            # for now, return destination path
            logger.info(f"downloading model {model_id} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"error downloading model {model_id}: {e}")
            raise

    def get_source_type(self) -> str:
        return "openuba_hub"

