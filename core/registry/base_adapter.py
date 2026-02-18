'''
Copyright 2019-Present The OpenUBA Platform Authors
base registry adapter interface
'''

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseRegistryAdapter(ABC):
    '''
    abstract base class for model registry adapters
    all adapters must implement these methods
    '''

    @abstractmethod
    def list_models(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list available models from this registry
        returns list of model metadata dicts
        '''
        pass

    @abstractmethod
    def fetch_model(self, model_id: str) -> Dict[str, Any]:
        '''
        fetch a specific model by id or reference
        returns model metadata and manifest
        '''
        pass

    @abstractmethod
    def get_manifest(self, model_id: str) -> Dict[str, Any]:
        '''
        get model manifest for a specific model
        manifest should include name, version, hashes, dependencies, etc.
        '''
        pass

    @abstractmethod
    def download_model(self, model_id: str, destination: str) -> str:
        '''
        download model files to destination directory
        returns path to downloaded model directory
        '''
        pass

    def normalize_manifest(self, raw_manifest: Dict[str, Any]) -> Dict[str, Any]:
        '''
        normalize manifest to common format
        subclasses can override to transform their specific format
        '''
        return {
            "name": raw_manifest.get("name"),
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
            "source_url": raw_manifest.get("source_url"),
        }

    @abstractmethod
    def get_source_type(self) -> str:
        '''
        return the source type identifier for this adapter
        '''
        pass

