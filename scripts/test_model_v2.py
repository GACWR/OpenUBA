import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.services.model_installer import ModelInstaller
from core.db import init_db, get_db_context
from core.repositories.model_repository import ModelRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_v2_lifecycle():
    logger.info("Starting Model V2 Lifecycle Test")

    # 1. Initialize DB
    logger.info("Initializing database...")
    init_db()

    # 2. Install Model
    logger.info("Installing model_1...")
    installer = ModelInstaller(dev_mode=True)
    
    # Point to the local model library
    # We use "local_fs" registry which looks in core/model_library by default
    # model_id is the directory name "model_1"
    try:
        model_id = installer.install_model(
            code_source_type="local_fs",
            model_id="model_1"
        )
        logger.info(f"Model installed successfully with ID: {model_id}")
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        return

    # 3. Verify in DB
    with get_db_context() as db:
        repo = ModelRepository(db)
        model = repo.get_by_id(model_id)
        if model:
            logger.info(f"Verified model in DB: {model.name} v{model.version}")
            logger.info(f"Manifest: {model.manifest}")
        else:
            logger.error("Model not found in DB after installation")
            return

    # 4. Simulate Execution (Train & Infer)
    logger.info("Simulating execution...")
    
    # Dynamic import of the installed model code
    # In a real runner, this happens in a separate process/container
    # Here we import from the source location for simplicity as installer copies it back to model_library anyway
    
    try:
        import importlib.util
        
        # The installer copies code to core/model_library/model_1 (or wherever MODEL_STORAGE_PATH points)
        # Let's assume it's in core/model_library/model_1 for this test
        model_path = project_root / "core" / "model_library" / "model_1" / "MODEL.py"
        
        spec = importlib.util.spec_from_file_location("MODEL", model_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Instantiate Model
        model_instance = module.Model()
        
        # Test Train
        logger.info("Testing train()...")
        train_result = model_instance.train(ctx={})
        logger.info(f"Train result: {train_result}")
        
        # Test Infer
        logger.info("Testing infer()...")
        infer_result = model_instance.infer(ctx={})
        logger.info(f"Infer result: {infer_result}")
        
        logger.info("Model V2 Lifecycle Test PASSED")

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_v2_lifecycle()
