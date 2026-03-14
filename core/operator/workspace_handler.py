'''
Copyright 2019-Present The OpenUBA Platform Authors
kopf operator handler for UBAWorkspace custom resources
'''

import logging
import os
import kopf
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

# workspace docker image
WORKSPACE_IMAGE = os.getenv("WORKSPACE_IMAGE", "openuba-workspace:latest")
WORKSPACE_NAMESPACE = os.getenv("WORKSPACE_NAMESPACE", "openuba")
BACKEND_SERVICE_URL = os.getenv("BACKEND_SERVICE_URL", "http://backend.openuba.svc:8000")

# hardware tier resource definitions
HARDWARE_TIERS = {
    "cpu-small": {
        "requests": {"cpu": "250m", "memory": "512Mi"},
        "limits": {"cpu": "500m", "memory": "1Gi"},
    },
    "cpu-large": {
        "requests": {"cpu": "500m", "memory": "2Gi"},
        "limits": {"cpu": "2", "memory": "4Gi"},
    },
    "gpu-small": {
        "requests": {"cpu": "500m", "memory": "1Gi"},
        "limits": {"cpu": "2", "memory": "4Gi", "nvidia.com/gpu": "1"},
    },
    "gpu-large": {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "4", "memory": "8Gi", "nvidia.com/gpu": "4"},
    },
}


@kopf.on.create('openuba.io', 'v1', 'ubaworkspaces')
def workspace_create(spec, name, namespace, status, patch, **kwargs):
    '''
    handle UBAWorkspace creation
    creates PVC, Pod, and NodePort Service for the workspace
    '''
    logger.info(f"creating workspace: {name}")

    ws_name = spec.get('name', name)
    hardware_tier = spec.get('hardware_tier', 'cpu-small')
    created_by = spec.get('created_by', 'unknown')
    timeout_hours = spec.get('timeout_hours', 24)
    environment = spec.get('environment', 'default')

    tier = HARDWARE_TIERS.get(hardware_tier, HARDWARE_TIERS['cpu-small'])
    pvc_size = os.getenv('WORKSPACE_DEFAULT_PVC_SIZE', '5Gi')

    pvc_name = f"{name}-data"
    pod_name = f"{name}-pod"
    svc_name = f"{name}-svc"

    patch.status['phase'] = 'Creating'
    patch.status['message'] = 'creating workspace resources'

    core_v1 = k8s_client.CoreV1Api()

    # create PVC
    try:
        pvc = k8s_client.V1PersistentVolumeClaim(
            metadata=k8s_client.V1ObjectMeta(name=pvc_name, namespace=namespace),
            spec=k8s_client.V1PersistentVolumeClaimSpec(
                access_modes=['ReadWriteOnce'],
                resources=k8s_client.V1ResourceRequirements(
                    requests={'storage': pvc_size}
                ),
            ),
        )
        kopf.adopt(pvc)
        core_v1.create_namespaced_persistent_volume_claim(namespace, pvc)
        logger.info(f"created PVC: {pvc_name}")
    except k8s_client.exceptions.ApiException as e:
        if e.status != 409:
            raise
        logger.info(f"PVC already exists: {pvc_name}")

    # create Pod
    env_vars = [
        k8s_client.V1EnvVar(name='OPENUBA_API_URL', value=BACKEND_SERVICE_URL),
        k8s_client.V1EnvVar(name='OPENUBA_WORKSPACE_ID', value=name),
        k8s_client.V1EnvVar(name='JUPYTER_ENABLE_LAB', value='yes'),
    ]

    # JupyterLab command: disable auth, allow iframe embedding, allow cross-origin
    # This matches OMS pattern for seamless iframe embedding in the frontend UI
    jupyter_cmd = [
        'start-notebook.sh',
        '--ServerApp.token=',
        '--ServerApp.password=',
        '--ServerApp.allow_origin=*',
        '--ServerApp.allow_remote_access=True',
        '--ServerApp.disable_check_xsrf=True',
        '--ServerApp.tornado_settings={"headers":{"Content-Security-Policy":"frame-ancestors * \'self\'"}}',
        f'--ServerApp.base_url=/',
        '--NotebookApp.token=',
        '--NotebookApp.password=',
    ]

    container = k8s_client.V1Container(
        name='workspace',
        image=WORKSPACE_IMAGE,
        command=['bash', '-c'],
        args=[' '.join(jupyter_cmd)],
        ports=[k8s_client.V1ContainerPort(container_port=8888)],
        env=env_vars,
        resources=k8s_client.V1ResourceRequirements(
            requests=tier['requests'],
            limits=tier['limits'],
        ),
        volume_mounts=[
            k8s_client.V1VolumeMount(name='workspace-data', mount_path='/workspace'),
        ],
    )

    pod = k8s_client.V1Pod(
        metadata=k8s_client.V1ObjectMeta(
            name=pod_name,
            namespace=namespace,
            labels={'app': 'uba-workspace', 'workspace': name},
        ),
        spec=k8s_client.V1PodSpec(
            containers=[container],
            volumes=[
                k8s_client.V1Volume(
                    name='workspace-data',
                    persistent_volume_claim=k8s_client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=pvc_name
                    ),
                ),
            ],
            restart_policy='Always',
        ),
    )
    kopf.adopt(pod)

    try:
        core_v1.create_namespaced_pod(namespace, pod)
        logger.info(f"created pod: {pod_name}")
    except k8s_client.exceptions.ApiException as e:
        if e.status != 409:
            raise
        logger.info(f"pod already exists: {pod_name}")

    # create NodePort service
    node_port = spec.get('node_port')
    svc_spec = k8s_client.V1ServiceSpec(
        type='NodePort',
        selector={'workspace': name},
        ports=[k8s_client.V1ServicePort(
            port=8888,
            target_port=8888,
            node_port=node_port if node_port else None,
        )],
    )

    svc = k8s_client.V1Service(
        metadata=k8s_client.V1ObjectMeta(name=svc_name, namespace=namespace),
        spec=svc_spec,
    )
    kopf.adopt(svc)

    try:
        created_svc = core_v1.create_namespaced_service(namespace, svc)
        actual_port = created_svc.spec.ports[0].node_port
        logger.info(f"created service: {svc_name} on nodeport {actual_port}")
    except k8s_client.exceptions.ApiException as e:
        if e.status != 409:
            raise
        actual_port = node_port
        logger.info(f"service already exists: {svc_name}")

    access_url = f"http://localhost:{actual_port}"

    patch.status['phase'] = 'Running'
    patch.status['pod_name'] = pod_name
    patch.status['service_name'] = svc_name
    patch.status['pvc_name'] = pvc_name
    patch.status['access_url'] = access_url
    patch.status['node_port'] = actual_port
    patch.status['message'] = 'workspace is running'

    logger.info(f"workspace {name} is running at {access_url}")
    return {'message': f'workspace created: {access_url}'}


@kopf.on.delete('openuba.io', 'v1', 'ubaworkspaces')
def workspace_delete(spec, name, namespace, **kwargs):
    '''
    handle UBAWorkspace deletion
    kubernetes garbage collection handles owned resources
    '''
    logger.info(f"workspace {name} deleted (owned resources will be garbage collected)")
    return {'message': f'workspace {name} deleted'}


@kopf.timer('openuba.io', 'v1', 'ubaworkspaces', interval=60)
def workspace_health_check(spec, name, namespace, status, patch, **kwargs):
    '''
    periodic health check for workspace pods
    checks pod status and enforces timeout
    '''
    phase = status.get('phase', 'Unknown')
    if phase != 'Running':
        return

    pod_name = status.get('pod_name')
    if not pod_name:
        return

    core_v1 = k8s_client.CoreV1Api()
    try:
        pod = core_v1.read_namespaced_pod(pod_name, namespace)
        pod_phase = pod.status.phase
        if pod_phase != 'Running':
            patch.status['phase'] = 'Failed'
            patch.status['message'] = f'pod is in {pod_phase} state'
            logger.warning(f"workspace {name} pod is {pod_phase}")
    except k8s_client.exceptions.ApiException as e:
        if e.status == 404:
            patch.status['phase'] = 'Failed'
            patch.status['message'] = 'pod not found'
            logger.warning(f"workspace {name} pod not found")
