'''
Copyright 2019-Present The OpenUBA Platform Authors
kubernetes utilities for e2e testing
'''

import os
import time
import logging
import subprocess
from typing import Optional, Dict, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class K8sTestUtils:
    '''
    utilities for interacting with kubernetes during e2e tests
    '''

    def __init__(self, namespace: str = "openuba"):
        self.namespace = namespace
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                raise Exception("could not load kubernetes config")

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def wait_for_pod_ready(
        self,
        label_selector: str,
        timeout: int = 300,
        check_interval: int = 5
    ) -> bool:
        '''
        wait for pods matching label selector to be ready
        '''
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=label_selector
                )
                if not pods.items:
                    time.sleep(check_interval)
                    continue

                all_ready = True
                for pod in pods.items:
                    if pod.status.phase != "Running":
                        all_ready = False
                        break
                    if not pod.status.container_statuses:
                        all_ready = False
                        break
                    for container in pod.status.container_statuses:
                        if not container.ready:
                            all_ready = False
                            break

                if all_ready:
                    logger.info(f"pods with selector {label_selector} are ready")
                    return True

                time.sleep(check_interval)
            except ApiException as e:
                logger.warning(f"error checking pod status: {e}")
                time.sleep(check_interval)

        logger.error(f"timeout waiting for pods with selector {label_selector}")
        return False

    def get_service_url(self, service_name: str, port: int) -> str:
        '''
        get service url for accessing from outside cluster
        returns localhost url if port-forwarding, or service url
        '''
        # for local testing, we'll use port-forwarding
        # in ci/cd, this might use ingress or nodeport
        return f"http://localhost:{port}"

    def port_forward_service(
        self,
        service_name: str,
        local_port: int,
        remote_port: int
    ) -> Optional[subprocess.Popen]:
        '''
        create port forward to service
        returns subprocess handle for cleanup
        '''
        cmd = [
            "kubectl", "port-forward",
            f"service/{service_name}",
            f"{local_port}:{remote_port}",
            "-n", self.namespace
        ]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # wait a bit for port forward to establish
            time.sleep(2)
            return process
        except Exception as e:
            logger.error(f"failed to create port forward: {e}")
            return None

    def get_pod_logs(
        self,
        label_selector: str,
        tail_lines: int = 100
    ) -> Dict[str, str]:
        '''
        get logs from pods matching label selector
        returns dict of pod_name -> logs
        '''
        logs = {}
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )
            for pod in pods.items:
                try:
                    pod_logs = self.core_v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=self.namespace,
                        tail_lines=tail_lines
                    )
                    logs[pod.metadata.name] = pod_logs
                except ApiException as e:
                    logger.warning(f"could not get logs for {pod.metadata.name}: {e}")
        except ApiException as e:
            logger.error(f"error listing pods: {e}")
        return logs

    def get_pod_names(self, label_selector: str) -> List[str]:
        '''
        get list of pod names matching label selector
        '''
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )
            return [pod.metadata.name for pod in pods.items]
        except ApiException as e:
            logger.error(f"error listing pods: {e}")
            return []

    def check_deployment_ready(self, deployment_name: str) -> bool:
        '''
        check if deployment is ready
        '''
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )
            return (
                deployment.status.ready_replicas == deployment.spec.replicas
                and deployment.status.ready_replicas is not None
            )
        except ApiException as e:
            logger.error(f"error checking deployment: {e}")
            return False

