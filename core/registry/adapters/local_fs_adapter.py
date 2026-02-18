'''
Copyright 2019-Present The OpenUBA Platform Authors
local filesystem adapter
'''

import os
import logging
import shutil
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from core.registry.base_adapter import BaseRegistryAdapter

logger = logging.getLogger(__name__)


class LocalFSAdapter(BaseRegistryAdapter):
    '''
    adapter for local filesystem model directory
    useful for development
    '''

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(
            base_path or os.getenv(
                "LOCAL_MODEL_PATH",
                "core/model_library"
            )
        )

    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list models in local filesystem
        looks for model.yaml files in subdirectories
        '''
        models = []
        if not self.base_path.exists():
            return models

        for model_dir in self.base_path.iterdir():
            if not model_dir.is_dir():
                continue
            model_yaml = model_dir / "model.yaml"
            if model_yaml.exists():
                try:
                    with open(model_yaml, "r") as f:
                        manifest = yaml.safe_load(f)
                    manifest["source_url"] = str(model_dir)
                    normalized = self.normalize_manifest(manifest)
                    if query:
                        if query.lower() in normalized.get("name", "").lower():
                            models.append(normalized)
                    else:
                        models.append(normalized)
                except Exception as e:
                    logger.debug(f"error reading {model_yaml}: {e}")

        return models

    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch model from local filesystem
        model_id is the directory name
        '''
        model_dir = self.base_path / model_id
        if not model_dir.exists():
            raise ValueError(f"model directory not found: {model_id}")

        model_yaml = model_dir / "model.yaml"
        if model_yaml.exists():
            with open(model_yaml, "r") as f:
                manifest = yaml.safe_load(f)
            manifest["source_url"] = str(model_dir)
            return self.normalize_manifest(manifest)
        else:
            # fallback: create manifest from directory structure
            return {
                "name": model_id,
                "version": "local",
                "source_url": str(model_dir),
                "components": []
            }

    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        return self.fetch_model(model_id)

    def download_model(self, model_id: str, destination: str) -> str:
        '''
        copy model from local filesystem to destination
        '''
        model_dir = self.base_path / model_id
        if not model_dir.exists():
            raise ValueError(f"model directory not found: {model_id}")

        os.makedirs(destination, exist_ok=True)
        shutil.copytree(model_dir, destination, dirs_exist_ok=True)
        logger.info(f"copied model {model_id} to {destination}")
        return destination

    def get_source_type(self) -> str:
        return "local_fs"

