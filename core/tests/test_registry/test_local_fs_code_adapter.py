'''
Copyright 2019-Present The OpenUBA Platform Authors
local filesystem code adapter tests
'''

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from core.registry.adapters.code.local_fs_code_adapter import LocalFSCodeAdapter


def test_list_models_empty_directory():
    '''
    test listing models from empty directory
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = LocalFSCodeAdapter(base_path=tmpdir)
        models = adapter.list_models()
        assert models == []


def test_list_models_with_manifest():
    '''
    test listing models with model.yaml files
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        # create a model directory with manifest
        model_dir = Path(tmpdir) / "test_model"
        model_dir.mkdir()
        manifest = {
            "name": "test_model",
            "version": "1.0.0",
            "description": "test model",
            "author": "test author"
        }
        with open(model_dir / "model.yaml", "w") as f:
            yaml.dump(manifest, f)
        
        adapter = LocalFSCodeAdapter(base_path=tmpdir)
        models = adapter.list_models()
        assert len(models) == 1
        assert models[0]["name"] == "test_model"
        assert models[0]["version"] == "1.0.0"


def test_fetch_model():
    '''
    test fetching a model by id
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        # create a model directory
        model_dir = Path(tmpdir) / "fetch_test_model"
        model_dir.mkdir()
        manifest = {
            "name": "fetch_test_model",
            "version": "1.0.0"
        }
        with open(model_dir / "model.yaml", "w") as f:
            yaml.dump(manifest, f)
        
        adapter = LocalFSCodeAdapter(base_path=tmpdir)
        model = adapter.fetch_model("fetch_test_model")
        assert model["name"] == "fetch_test_model"
        assert model["version"] == "1.0.0"


def test_download_model():
    '''
    test downloading model code
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        # create a model directory with files
        model_dir = Path(tmpdir) / "download_test_model"
        model_dir.mkdir()
        (model_dir / "model.py").write_text("print('test')")
        manifest = {
            "name": "download_test_model",
            "version": "1.0.0"
        }
        with open(model_dir / "model.yaml", "w") as f:
            yaml.dump(manifest, f)
        
        adapter = LocalFSCodeAdapter(base_path=tmpdir)
        dest = tempfile.mkdtemp()
        try:
            result = adapter.download_model("download_test_model", dest)
            assert Path(dest).exists()
            assert (Path(dest) / "model.py").exists()
            assert (Path(dest) / "model.yaml").exists()
        finally:
            shutil.rmtree(dest)

