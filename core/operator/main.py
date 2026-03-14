import kopf
import kubernetes
import yaml
import os
import json

# import workspace handler to register its kopf handlers
try:
    import workspace_handler  # noqa: F401
except ImportError:
    try:
        import core.operator.workspace_handler  # noqa: F401
    except ImportError:
        pass

# import pipeline handler to register its kopf handlers
try:
    import pipeline_handler  # noqa: F401
except ImportError:
    try:
        import core.operator.pipeline_handler  # noqa: F401
    except ImportError:
        pass

# Setup K8s client
if os.getenv("KUBERNETES_SERVICE_HOST"):
    kubernetes.config.load_incluster_config()
else:
    try:
        kubernetes.config.load_kube_config()
    except:
        pass  # Will fail later if no config

core_api = kubernetes.client.CoreV1Api()
batch_api = kubernetes.client.BatchV1Api()

def create_job_manifest(name, image, args, env_vars, pvc_name="model-storage-pvc"):
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": name,
            "namespace": os.getenv("KUBERNETES_NAMESPACE", "openuba")
        },
        "spec": {
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [{
                        "name": "runner",
                        "image": image,
                        "imagePullPolicy": "IfNotPresent",
                        "args": args,
                        "env": env_vars,
                        "volumeMounts": [{
                            "name": "model-data",
                            "mountPath": "/model",
                            "readOnly": False
                        }, {
                            "name": "system-data",
                            "mountPath": "/system",
                            "readOnly": False
                        }, {
                            "name": "saved-models",
                            "mountPath": "/opt/openuba/saved_models",
                            "readOnly": False
                        }, {
                            "name": "datasets",
                            "mountPath": "/app/test_datasets",
                            "readOnly": True
                        }]
                    }],
                    "volumes": [{
                        "name": "model-data",
                        "persistentVolumeClaim": {
                            "claimName": pvc_name
                        }
                    }, {
                        "name": "system-data",
                        "persistentVolumeClaim": {
                            "claimName": "system-storage-pvc"
                        }
                    }, {
                        "name": "saved-models",
                        "persistentVolumeClaim": {
                            "claimName": "saved-models-pvc"
                        }
                    }, {
                        "name": "datasets",
                        "persistentVolumeClaim": {
                            "claimName": "datasets-pvc"
                        }
                    }]
                }
            },
            "backoffLimit": 0,
            "ttlSecondsAfterFinished": 300 # Cleanup successful jobs after 5 mins
        }
    }

@kopf.on.create('openuba.io', 'v1alpha1', 'ubainferences')
def create_inference_job(spec, name, meta, status, **kwargs):
    runtime = spec.get('runtime', 'python-base')
    input_path = spec.get('inputPath')
    output_path = spec.get('outputPath')
    model_ref = spec.get('modelRef')

    # Resolve runtime to image
    image_tag = "base"
    if runtime in ["sklearn", "pytorch", "tensorflow", "networkx"]:
        image_tag = runtime
    image = f"openuba-model-runner:{image_tag}"

    job_name = f"inf-job-{name}"

    # Env vars for the runner
    db_url = os.getenv("DATABASE_URL", "postgresql://gacwr:gacwr@postgres.openuba.svc:5432/openuba")
    run_id = spec.get('runId', '')
    execution_id = spec.get('executionId', '')
    model_slug = spec.get('modelSlug', model_ref)
    model_version = spec.get('modelVersion', '1.0.0')
    artifact_path = spec.get('artifactPath', '')
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
    env = [
        {"name": "RUN_TYPE", "value": "infer"},
        {"name": "UBA_INPUT_PATH", "value": input_path},
        {"name": "UBA_OUTPUT_PATH", "value": output_path},
        {"name": "MODEL_ID", "value": model_ref},
        {"name": "MODEL_PATH", "value": "/model/" + model_ref},
        {"name": "DATABASE_URL", "value": db_url},
        {"name": "RUN_ID", "value": run_id},
        {"name": "EXECUTION_ID", "value": execution_id},
        {"name": "MODEL_SLUG", "value": model_slug},
        {"name": "MODEL_VERSION", "value": model_version},
        {"name": "MODEL_RUNTIME", "value": runtime},
        {"name": "SAVED_MODELS_PATH", "value": "/opt/openuba/saved_models"},
        {"name": "ELASTICSEARCH_HOST", "value": es_host},
        {"name": "ARTIFACT_PATH", "value": artifact_path}
    ]

    job_manifest = create_job_manifest(job_name, image, ["infer"], env)

    # Adopt the job so it gets deleted with the CRD
    kopf.adopt(job_manifest)

    try:
        obj = batch_api.create_namespaced_job(
            namespace=meta['namespace'],
            body=job_manifest
        )
        return {'phase': 'Running', 'message': f"Job {job_name} created"}
    except kubernetes.client.rest.ApiException as e:
        raise kopf.PermanentError(f"Failed to create job: {e}")

@kopf.on.create('openuba.io', 'v1alpha1', 'ubatrainings')
def create_training_job(spec, name, meta, status, **kwargs):
    runtime = spec.get('runtime', 'python-base')
    config_path = spec.get('configPath')
    output_path = spec.get('outputPath')
    model_ref = spec.get('modelRef')

    # Resolve runtime
    image_tag = "base"
    if runtime in ["sklearn", "pytorch", "tensorflow", "networkx"]:
        image_tag = runtime
    image = f"openuba-model-runner:{image_tag}"

    job_name = f"train-job-{name}"

    # Env vars for training
    db_url = os.getenv("DATABASE_URL", "postgresql://gacwr:gacwr@postgres.openuba.svc:5432/openuba")
    run_id = spec.get('runId', '')
    execution_id = spec.get('executionId', '')
    model_slug = spec.get('modelSlug', model_ref)
    model_version = spec.get('modelVersion', '1.0.0')
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
    env = [
        {"name": "RUN_TYPE", "value": "train"},
        {"name": "UBA_CONFIG_PATH", "value": config_path},
        {"name": "UBA_OUTPUT_PATH", "value": output_path},
        {"name": "MODEL_ID", "value": model_ref},
        {"name": "MODEL_PATH", "value": "/model/" + model_ref},
        {"name": "DATABASE_URL", "value": db_url},
        {"name": "RUN_ID", "value": run_id},
        {"name": "EXECUTION_ID", "value": execution_id},
        {"name": "MODEL_SLUG", "value": model_slug},
        {"name": "MODEL_VERSION", "value": model_version},
        {"name": "MODEL_RUNTIME", "value": runtime},
        {"name": "SAVED_MODELS_PATH", "value": "/opt/openuba/saved_models"},
        {"name": "ELASTICSEARCH_HOST", "value": es_host}
    ]

    job_manifest = create_job_manifest(job_name, image, ["train"], env)
    kopf.adopt(job_manifest)

    try:
        batch_api.create_namespaced_job(
            namespace=meta['namespace'],
            body=job_manifest
        )
        return {'phase': 'Running', 'message': f"Training Job {job_name} created"}
    except kubernetes.client.rest.ApiException as e:
        raise kopf.PermanentError(f"Failed to create job: {e}")

@kopf.on.event('batch', 'v1', 'jobs')
def job_event(event, body, **kwargs):
    # Watch for completion of our jobs
    job_name = body['metadata']['name']

    # Determine type
    crd_type = None
    if job_name.startswith('inf-job-'):
        crd_type = "ubainferences"
        prefix_len = 8
    elif job_name.startswith('train-job-'):
        crd_type = "ubatrainings"
        prefix_len = 10
    else:
        return

    # Infer parent CRD name
    parent_crd_name = job_name[prefix_len:]

    status = body.get('status', {})
    if status.get('succeeded'):
        # Update CRD
        try:
            api = kubernetes.client.CustomObjectsApi()
            patch = {
                "status": {
                    "phase": "Succeeded",
                    "completedAt": status.get('completionTime')
                }
            }
            if crd_type == "ubainferences":
                 patch["status"]["resultReady"] = True

            api.patch_namespaced_custom_object_status(
                group="openuba.io",
                version="v1alpha1",
                namespace=body['metadata']['namespace'],
                plural=crd_type,
                name=parent_crd_name,
                body=patch
            )
        except Exception as e:
            print(f"Failed to update CRD status: {e}")

    elif status.get('failed'):
        try:
            api = kubernetes.client.CustomObjectsApi()
            patch = {
                "status": {
                    "phase": "Failed",
                    "message": "Job failed"
                }
            }
            api.patch_namespaced_custom_object_status(
                group="openuba.io",
                version="v1alpha1",
                namespace=body['metadata']['namespace'],
                plural=crd_type,
                name=parent_crd_name,
                body=patch
            )
        except Exception as e:
            print(f"Failed to update CRD status: {e}")
