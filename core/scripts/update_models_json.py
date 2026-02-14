
import os
import json
import hashlib
import base64
from pathlib import Path

MODEL_LIBRARY_PATH = Path("core/model_library")
MODELS_JSON_PATH = Path("core/storage/models.json")

def compute_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_payload(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def scan_models():
    models_config = {}
    
    if MODELS_JSON_PATH.exists():
        with open(MODELS_JSON_PATH, "r") as f:
            try:
                models_config = json.load(f)
            except json.JSONDecodeError:
                print("Warning: existing models.json is invalid, starting fresh")
                models_config = {}

    # Define a group for our real models
    group_name = "REAL_MODELS_GROUP"
    
    real_models = []
    
    # Iterate over directories in model library
    for model_dir in MODEL_LIBRARY_PATH.iterdir():
        if model_dir.is_dir() and not model_dir.name.startswith(('.', '__')) and "backup" not in model_dir.name and "test" not in model_dir.name and "dummy" not in model_dir.name:
            
            model_name = model_dir.name
            print(f"Processing model: {model_name}")
            
            components = []
            
            # Look for standard files
            for file_path in model_dir.glob("*"):
                if file_path.is_file() and file_path.name != "__pycache__":
                    components.append({
                        "type": "external",
                        "filename": file_path.name,
                        "data_hash": compute_file_hash(file_path), # Using file hash as data hash for simplicity
                        "file_hash": compute_file_hash(file_path),
                        "file_payload": get_file_payload(file_path)
                    })
            
            if not components:
                print(f"Skipping empty model: {model_name}")
                continue

            # Read metadata from model.yaml if exists
            model_yaml_path = model_dir / "model.yaml"
            runtime = "python-base"
            description = f"Auto-generated entry for {model_name}"
            
            if model_yaml_path.exists():
                try:
                    import yaml
                    with open(model_yaml_path, "r") as f:
                        manifest = yaml.safe_load(f)
                        runtime = manifest.get("runtime", "python-base")
                        description = manifest.get("description", description)
                except ImportError:
                   print("Warning: PyYAML not installed, skipping yaml parse")
                except Exception as e:
                   print(f"Warning: failed to parse {model_yaml_path}: {e}")

            model_entry = {
                "model_name": model_name,
                "description": description,
                "mitre_tactic": "Defense Evasion",
                "mitre_technique_name": "Indicator Removal",
                "mitre_technique_id": "T1070",
                "enabled": True,
                "root": "AUTO_GENERATED", 
                "runtime": runtime,
                "return": {
                    "return_type": "user_risks",
                    "artifacts": []
                },
                "score": 50,
                "model_context": {},
                "components": components
            }
            real_models.append(model_entry)

    # valid data loader context
    data_loader = {
      "data_loader_type": "local_pandas_csv",
      "data_loader_context": {
        "file_location": "../test_datasets/", 
        "file": "dummy.csv"
      }
    }

    models_config[group_name] = {
        "group_name": group_name,
        "data_loader": data_loader,
        "model_group_context": {"rules": []},
        "models": real_models
    }
    
    # Write back
    with open(MODELS_JSON_PATH, "w") as f:
        json.dump(models_config, f, indent=2)
        
    print(f"Updated {MODELS_JSON_PATH} with {len(real_models)} real models.")

if __name__ == "__main__":
    scan_models()
