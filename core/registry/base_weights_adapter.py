'''
Copyright 2019-Present The OpenUBA Platform Authors
base weights registry adapter interface
'''

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseWeightsAdapter(ABC):
    '''
    abstract base class for model weights registry adapters
    weights adapters handle trained model weights/artifacts
    separate from model code registries
    '''

    @abstractmethod
    def list_weights(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        list available weights for a model or all weights
        returns list of weights metadata dicts
        '''
        pass

    @abstractmethod
    def fetch_weights(self, weights_id: str) -> Dict[str, Any]:
        '''
        fetch specific weights by id or reference
        returns weights metadata
        '''
        pass

    @abstractmethod
    def download_weights(self, weights_id: str, destination: str) -> str:
        '''
        download weights files to destination directory
        returns path to downloaded weights directory
        '''
        pass

    def normalize_weights_manifest(self, raw_manifest: Dict[str, Any]) -> Dict[str, Any]:
        '''
        normalize weights manifest to common format
        subclasses can override to transform their specific format
        '''
        return {
            "weights_id": raw_manifest.get("weights_id"),
            "model_name": raw_manifest.get("model_name"),
            "version": raw_manifest.get("version"),
            "format": raw_manifest.get("format"),  # e.g., pytorch, tensorflow, onnx
            "size": raw_manifest.get("size"),
            "checksum": raw_manifest.get("checksum"),
            "source_type": self.get_source_type(),
            "source_url": raw_manifest.get("source_url")
        }

    @abstractmethod
    def get_source_type(self) -> str:
        '''
        return the source type identifier for this adapter
        '''
        pass

