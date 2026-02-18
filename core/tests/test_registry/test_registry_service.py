'''
Copyright 2019-Present The OpenUBA Platform Authors
registry service tests
'''

import pytest
import os
from core.registry import RegistryService


def test_registry_service_initialization():
    '''
    test that registry service initializes with adapters
    '''
    service = RegistryService()
    assert len(service.code_adapters) > 0
    assert len(service.weights_adapters) > 0
    assert "local_fs" in service.code_adapters


def test_default_code_registry():
    '''
    test default code registry selection
    '''
    # test dev mode (default)
    service = RegistryService()
    assert service.default_code_registry == "local_fs"
    
    # test production mode
    os.environ["ENVIRONMENT"] = "production"
    service_prod = RegistryService()
    assert service_prod.default_code_registry == "github"
    del os.environ["ENVIRONMENT"]


def test_get_code_adapter():
    '''
    test getting code adapter
    '''
    service = RegistryService()
    adapter = service.get_code_adapter("local_fs")
    assert adapter is not None
    assert adapter.get_source_type() == "local_fs"


def test_get_weights_adapter():
    '''
    test getting weights adapter
    '''
    service = RegistryService()
    adapter = service.get_weights_adapter("local_fs")
    assert adapter is not None
    assert adapter.get_source_type() == "local_fs"


def test_search_models_code():
    '''
    test searching code models
    '''
    service = RegistryService()
    results = service.search_models("test", registry_type="code")
    assert isinstance(results, list)


def test_search_models_weights():
    '''
    test searching weights
    '''
    service = RegistryService()
    results = service.search_models("test", registry_type="weights")
    assert isinstance(results, list)

