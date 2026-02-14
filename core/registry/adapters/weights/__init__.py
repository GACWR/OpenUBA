'''
Copyright 2019-Present The OpenUBA Platform Authors
weights registry adapters
'''

from core.registry.adapters.weights.huggingface_weights_adapter import HuggingFaceWeightsAdapter
from core.registry.adapters.weights.kubeflow_weights_adapter import KubeflowWeightsAdapter
from core.registry.adapters.weights.local_fs_weights_adapter import LocalFSWeightsAdapter

__all__ = [
    "HuggingFaceWeightsAdapter",
    "KubeflowWeightsAdapter",
    "LocalFSWeightsAdapter"
]

