'''
Copyright 2019-Present The OpenUBA Platform Authors
local filesystem weights adapter
'''

import os
import logging
import shutil
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from core.registry.base_weights_adapter import BaseWeightsAdapter

logger = logging.getLogger(__name__)


class LocalFSWeightsAdapter(BaseWeightsAdapter):
    '''
    adapter for local filesystem model weights directory
    useful for development
    '''

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(
            base_path or os.getenv(
                "LOCAL_MODEL_WEIGHTS_PATH",
                "core/model_library"
            )
        )

    def list_weights(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list weights in local filesystem
        looks for weights.yaml files in subdirectories
        '''
        weights = []
        if not self.base_path.exists():
            return weights

        for weights_dir in self.base_path.iterdir():
            if not weights_dir.is_dir():
                continue
            weights_yaml = weights_dir / "weights.yaml"
            if weights_yaml.exists():
                try:
                    with open(weights_yaml, "r") as f:
                        manifest = yaml.safe_load(f)
                    manifest["source_url"] = str(weights_dir)
                    normalized = self.normalize_weights_manifest(manifest)
                    if model_name:
                        if model_name.lower() in normalized.get("model_name", "").lower():
                            weights.append(normalized)
                    else:
                        weights.append(normalized)
                except Exception as e:
                    logger.debug(f"error reading {weights_yaml}: {e}")

        return weights

    def fetch_weights(self, weights_id: str) -> Dict[str, Any]:
        '''
        fetch weights from local filesystem
        weights_id is the directory name
        '''
        weights_dir = self.base_path / weights_id
        if not weights_dir.exists():
            raise ValueError(f"weights directory not found: {weights_id}")

        weights_yaml = weights_dir / "weights.yaml"
        if weights_yaml.exists():
            with open(weights_yaml, "r") as f:
                manifest = yaml.safe_load(f)
            manifest["source_url"] = str(weights_dir)
            return self.normalize_weights_manifest(manifest)
        else:
            # fallback: create manifest from directory structure
            return {
                "weights_id": weights_id,
                "model_name": weights_id,
                "version": "local",
                "source_url": str(weights_dir),
                "format": "unknown"
            }

    def download_weights(self, weights_id: str, destination: str) -> str:
        '''
        copy weights from local filesystem to destination
        '''
        weights_dir = self.base_path / weights_id
        if not weights_dir.exists():
            raise ValueError(f"weights directory not found: {weights_id}")

        os.makedirs(destination, exist_ok=True)
        shutil.copytree(weights_dir, destination, dirs_exist_ok=True)
        logger.info(f"copied weights {weights_id} to {destination}")
        return destination

    def get_source_type(self) -> str:
        return "local_fs"

