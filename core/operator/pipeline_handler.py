'''
Copyright 2019-Present The OpenUBA Platform Authors
kopf handler for UBAPipeline custom resources
executes pipeline steps sequentially, creating training/inference CRDs for each step
'''

import kopf
import kubernetes
import os
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NAMESPACE = os.getenv("KUBERNETES_NAMESPACE", "openuba")


@kopf.on.create('openuba.io', 'v1', 'ubapipelines')
def create_pipeline(spec, name, meta, status, patch, **kwargs):
    '''
    handle creation of a UBAPipeline CR
    kicks off the first step of the pipeline
    '''
    steps = spec.get('steps', [])
    if not steps:
        raise kopf.PermanentError("pipeline has no steps")

    pipeline_name = spec.get('name', name)
    created_by = spec.get('created_by', 'system')

    logger.info(f"pipeline created: {pipeline_name} with {len(steps)} steps")

    # initialize step statuses
    step_statuses = []
    for i, step in enumerate(steps):
        step_statuses.append({
            "step_index": i,
            "status": "pending",
            "message": f"step {i}: {step.get('type', 'unknown')}",
        })

    # update status to Running and kick off first step
    patch.status['phase'] = 'Running'
    patch.status['current_step'] = 0
    patch.status['step_statuses'] = step_statuses
    patch.status['started_at'] = datetime.now(timezone.utc).isoformat()

    _execute_step(name, meta['namespace'], steps[0], 0, created_by)

    return {'phase': 'Running', 'message': f'Pipeline started with {len(steps)} steps'}


def _execute_step(pipeline_name, namespace, step, step_index, created_by):
    '''
    execute a single pipeline step by creating the appropriate CRD
    '''
    step_type = step.get('type', 'training')
    model_id = step.get('model_id', '')
    dataset_id = step.get('dataset_id', '')
    hardware_tier = step.get('hardware_tier', 'cpu-small')
    hyperparameters = step.get('hyperparameters', {})

    cr_name = f"pipe-{pipeline_name}-step-{step_index}"

    if step_type == 'training':
        body = {
            "apiVersion": "openuba.io/v1alpha1",
            "kind": "UBATraining",
            "metadata": {
                "name": cr_name,
                "namespace": namespace,
                "labels": {
                    "openuba.io/pipeline": pipeline_name,
                    "openuba.io/step-index": str(step_index),
                },
            },
            "spec": {
                "modelRef": model_id,
                "runtime": "python-base",
                "configPath": "",
                "outputPath": f"/model/{model_id}/output",
                "hardwareTier": hardware_tier,
                "datasetId": dataset_id,
                "hyperparameters": hyperparameters,
            },
        }
        plural = "ubatrainings"
    elif step_type == 'inference':
        body = {
            "apiVersion": "openuba.io/v1alpha1",
            "kind": "UBAInference",
            "metadata": {
                "name": cr_name,
                "namespace": namespace,
                "labels": {
                    "openuba.io/pipeline": pipeline_name,
                    "openuba.io/step-index": str(step_index),
                },
            },
            "spec": {
                "modelRef": model_id,
                "runtime": "python-base",
                "inputPath": f"/data/{dataset_id}",
                "outputPath": f"/model/{model_id}/predictions",
                "datasetId": dataset_id,
            },
        }
        plural = "ubainferences"
    else:
        logger.warning(f"unknown step type: {step_type}, treating as training")
        return

    try:
        api = kubernetes.client.CustomObjectsApi()
        api.create_namespaced_custom_object(
            group="openuba.io",
            version="v1alpha1",
            namespace=namespace,
            plural=plural,
            body=body,
        )
        logger.info(f"pipeline step {step_index} CRD created: {cr_name}")
    except kubernetes.client.rest.ApiException as e:
        logger.error(f"failed to create step CRD: {e}")
        raise kopf.TemporaryError(f"failed to create step {step_index}: {e}", delay=30)


@kopf.on.event('batch', 'v1', 'jobs', labels={'openuba.io/pipeline': kopf.PRESENT})
def pipeline_job_event(event, body, labels, **kwargs):
    '''
    watch for completion of pipeline step jobs
    when a step completes, advance to the next step or mark pipeline complete
    '''
    pipeline_name = labels.get('openuba.io/pipeline')
    step_index_str = labels.get('openuba.io/step-index')
    if not pipeline_name or step_index_str is None:
        return

    step_index = int(step_index_str)
    job_status = body.get('status', {})

    if not job_status.get('succeeded') and not job_status.get('failed'):
        return

    try:
        api = kubernetes.client.CustomObjectsApi()
        namespace = body['metadata']['namespace']

        # get the pipeline CR
        pipeline = api.get_namespaced_custom_object(
            group="openuba.io",
            version="v1",
            namespace=namespace,
            plural="ubapipelines",
            name=pipeline_name,
        )

        steps = pipeline.get('spec', {}).get('steps', [])
        current_status = pipeline.get('status', {})
        step_statuses = current_status.get('step_statuses', [])

        if job_status.get('succeeded'):
            # mark step as completed
            if step_index < len(step_statuses):
                step_statuses[step_index]['status'] = 'completed'
                step_statuses[step_index]['message'] = 'Step completed successfully'

            next_step = step_index + 1
            if next_step < len(steps):
                # advance to next step
                patch = {
                    "status": {
                        "current_step": next_step,
                        "step_statuses": step_statuses,
                    }
                }
                api.patch_namespaced_custom_object_status(
                    group="openuba.io", version="v1",
                    namespace=namespace, plural="ubapipelines",
                    name=pipeline_name, body=patch,
                )
                created_by = pipeline.get('spec', {}).get('created_by', 'system')
                _execute_step(pipeline_name, namespace, steps[next_step], next_step, created_by)
            else:
                # pipeline complete
                patch = {
                    "status": {
                        "phase": "Completed",
                        "step_statuses": step_statuses,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
                api.patch_namespaced_custom_object_status(
                    group="openuba.io", version="v1",
                    namespace=namespace, plural="ubapipelines",
                    name=pipeline_name, body=patch,
                )
                logger.info(f"pipeline {pipeline_name} completed all steps")

        elif job_status.get('failed'):
            # mark step and pipeline as failed
            if step_index < len(step_statuses):
                step_statuses[step_index]['status'] = 'failed'
                step_statuses[step_index]['message'] = 'Step failed'

            patch = {
                "status": {
                    "phase": "Failed",
                    "step_statuses": step_statuses,
                    "message": f"Step {step_index} failed",
                }
            }
            api.patch_namespaced_custom_object_status(
                group="openuba.io", version="v1",
                namespace=namespace, plural="ubapipelines",
                name=pipeline_name, body=patch,
            )
            logger.error(f"pipeline {pipeline_name} failed at step {step_index}")

    except Exception as e:
        logger.error(f"failed to process pipeline job event: {e}")
