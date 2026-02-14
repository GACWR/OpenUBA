'''
Copyright 2019-Present The OpenUBA Platform Authors
registry service - unified interface to multiple registries (code and weights)
'''

import os
import logging
from typing import List, Dict, Any, Optional
from core.registry.base_adapter import BaseRegistryAdapter
from core.registry.base_weights_adapter import BaseWeightsAdapter

# code adapters
from core.registry.adapters.code.openuba_hub_code_adapter import OpenUBAHubCodeAdapter
from core.registry.adapters.code.github_code_adapter import GitHubCodeAdapter
from core.registry.adapters.code.local_fs_code_adapter import LocalFSCodeAdapter

# weights adapters
from core.registry.adapters.weights.huggingface_weights_adapter import HuggingFaceWeightsAdapter
from core.registry.adapters.weights.kubeflow_weights_adapter import KubeflowWeightsAdapter
from core.registry.adapters.weights.local_fs_weights_adapter import LocalFSWeightsAdapter

logger = logging.getLogger(__name__)


class RegistryService:
    '''
    unified service for querying multiple model registries
    supports both code registries and weights registries
    '''

    def __init__(self):
        self.code_adapters: Dict[str, BaseRegistryAdapter] = {}
        self.weights_adapters: Dict[str, BaseWeightsAdapter] = {}
        self._initialize_adapters()
        self._set_defaults()

    def _initialize_adapters(self) -> None:
        '''
        initialize all available code and weights adapters
        '''
        # initialize code adapters
        try:
            self.code_adapters["openuba_hub"] = OpenUBAHubCodeAdapter()
        except Exception as e:
            logger.warning(f"openuba hub code adapter not available: {e}")

        try:
            self.code_adapters["github"] = GitHubCodeAdapter()
        except Exception as e:
            logger.warning(f"github code adapter not available: {e}")

        try:
            self.code_adapters["local_fs"] = LocalFSCodeAdapter()
        except Exception as e:
            logger.warning(f"local filesystem code adapter not available: {e}")

        # initialize weights adapters
        try:
            self.weights_adapters["huggingface"] = HuggingFaceWeightsAdapter()
        except Exception as e:
            logger.warning(f"huggingface weights adapter not available: {e}")

        try:
            self.weights_adapters["kubeflow"] = KubeflowWeightsAdapter()
        except Exception as e:
            logger.warning(f"kubeflow weights adapter not available: {e}")

        try:
            self.weights_adapters["local_fs"] = LocalFSWeightsAdapter()
        except Exception as e:
            logger.warning(f"local filesystem weights adapter not available: {e}")

    def _set_defaults(self) -> None:
        '''
        set default registries based on environment
        local_fs for dev, github for production (code)
        '''
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            self.default_code_registry = os.getenv("DEFAULT_CODE_REGISTRY", "github")
        else:
            self.default_code_registry = os.getenv("DEFAULT_CODE_REGISTRY", "local_fs")

        self.default_weights_registry = os.getenv("DEFAULT_WEIGHTS_REGISTRY", "local_fs")

    def search_models(
        self,
        query: str,
        source_types: Optional[List[str]] = None,
        registry_type: str = "code"
    ) -> List[Dict[str, Any]]:
        '''
        search for models across registries
        registry_type: "code", "weights", or "all" (searches both)
        '''
        results = []
        
        # if "all", search both code and weights registries
        if registry_type == "all":
            # search code registries
            code_results = self.search_models(query, source_types, "code")
            results.extend(code_results)
            
            # search weights registries
            weights_results = self.search_models(query, source_types, "weights")
            results.extend(weights_results)
            
            return results
        
        if registry_type == "code":
            adapters_to_search = self.code_adapters
            if source_types:
                adapters_to_search = {
                    k: v for k, v in self.code_adapters.items()
                    if k in source_types
                }

            for source_type, adapter in adapters_to_search.items():
                try:
                    models = adapter.list_models(query=query)
                    for model in models:
                        model["source_type"] = source_type
                        model["registry_type"] = "code"
                    results.extend(models)
                except Exception as e:
                    logger.error(f"error searching {source_type}: {e}")
        else:  # weights
            adapters_to_search = self.weights_adapters
            if source_types:
                adapters_to_search = {
                    k: v for k, v in self.weights_adapters.items()
                    if k in source_types
                }

            for source_type, adapter in adapters_to_search.items():
                try:
                    weights = adapter.list_weights(model_name=query)
                    for weight in weights:
                        weight["source_type"] = source_type
                        weight["registry_type"] = "weights"
                    results.extend(weights)
                except Exception as e:
                    logger.error(f"error searching weights {source_type}: {e}")

        return results

    def get_code_adapter(self, source_type: Optional[str] = None) -> Optional[BaseRegistryAdapter]:
        '''
        get code adapter for a specific source type or default
        '''
        if not source_type:
            source_type = self.default_code_registry
        return self.code_adapters.get(source_type)

    def get_weights_adapter(self, source_type: Optional[str] = None) -> Optional[BaseWeightsAdapter]:
        '''
        get weights adapter for a specific source type or default
        '''
        if not source_type:
            source_type = self.default_weights_registry
        return self.weights_adapters.get(source_type)

    def fetch_model(
        self,
        source_type: Optional[str] = None,
        model_id: str = "",
        registry_type: str = "code"
    ) -> Optional[Dict[str, Any]]:
        '''
        fetch a model from a specific registry
        uses default registry if source_type not provided
        '''
        if registry_type == "code":
            adapter = self.get_code_adapter(source_type)
            if not adapter:
                return None
            try:
                return adapter.fetch_model(model_id)
            except Exception as e:
                logger.error(f"error fetching model from {source_type or self.default_code_registry}: {e}")
                return None
        else:  # weights
            adapter = self.get_weights_adapter(source_type)
            if not adapter:
                return None
            try:
                return adapter.fetch_weights(model_id)
            except Exception as e:
                logger.error(f"error fetching weights from {source_type or self.default_weights_registry}: {e}")
                return None

    def download_model(
        self,
        source_type: Optional[str] = None,
        model_id: str = "",
        destination: str = "",
        registry_type: str = "code"
    ) -> Optional[str]:
        '''
        download a model from a specific registry
        uses default registry if source_type not provided
        '''
        if registry_type == "code":
            adapter = self.get_code_adapter(source_type)
            if not adapter:
                return None
            try:
                return adapter.download_model(model_id, destination)
            except Exception as e:
                logger.error(f"error downloading model from {source_type or self.default_code_registry}: {e}")
                return None
        else:  # weights
            adapter = self.get_weights_adapter(source_type)
            if not adapter:
                return None
            try:
                return adapter.download_weights(model_id, destination)
            except Exception as e:
                logger.error(f"error downloading weights from {source_type or self.default_weights_registry}: {e}")
                return None

    # backward compatibility methods
    def get_adapter(self, source_type: str) -> Optional[BaseRegistryAdapter]:
        '''
        get code adapter (backward compatibility)
        '''
        return self.get_code_adapter(source_type)
