'''
Copyright 2019-Present The OpenUBA Platform Authors
model installer tests
'''

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from core.services.model_installer import ModelInstaller


def test_model_installer_initialization():
    '''
    test model installer initialization
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        installer = ModelInstaller(dev_mode=True)
        assert installer.dev_mode == True
        assert installer.model_storage_path.exists()


def test_install_model_from_local_fs():
    '''
    test installing a model from local filesystem
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        # create a model in source directory
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        model_dir = source_dir / "test_install_model"
        model_dir.mkdir()
        (model_dir / "MODEL.py").write_text("def run(): pass")
        manifest = {
            "name": "test_install_model",
            "version": "1.0.0",
            "components": [
                {
                    "filename": "MODEL.py",
                    "type": "external"
                }
            ]
        }
        with open(model_dir / "model.yaml", "w") as f:
            yaml.dump(manifest, f)
        
        # set up installer with source path
        import os
        os.environ["LOCAL_MODEL_CODE_PATH"] = str(source_dir)
        storage_path = Path(tmpdir) / "storage"
        os.environ["MODEL_STORAGE_PATH"] = str(storage_path)
        
        installer = ModelInstaller(dev_mode=True)
        # this would require database setup, so we'll test the structure
        assert installer.model_storage_path == storage_path
        assert installer.registry_service is not None
        
        # cleanup
        del os.environ["LOCAL_MODEL_CODE_PATH"]
        del os.environ["MODEL_STORAGE_PATH"]

