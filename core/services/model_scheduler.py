'''
Copyright 2019-Present The OpenUBA Platform Authors
model execution scheduler
supports both kubernetes cronjobs and apscheduler
'''

import os
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.db import get_db_context
from core.repositories.model_repository import ModelRepository
from core.services.model_orchestrator import ModelOrchestrator

logger = logging.getLogger(__name__)


class ModelScheduler:
    '''
    manages scheduled model executions
    supports kubernetes cronjobs and apscheduler
    '''

    def __init__(self):
        self.execution_mode = os.getenv("EXECUTION_MODE", "docker")
        self.scheduler_type = os.getenv("SCHEDULER_TYPE", "apscheduler")  # apscheduler or kubernetes
        self.orchestrator = ModelOrchestrator()
        self.apscheduler = None
        self._init_scheduler()

    def _init_scheduler(self) -> None:
        '''
        initialize scheduler based on type
        '''
        if self.scheduler_type == "apscheduler":
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from apscheduler.triggers.cron import CronTrigger
                self.apscheduler = BackgroundScheduler()
                self.apscheduler.start()
                logger.info("apscheduler initialized")
            except ImportError:
                logger.warning("apscheduler not installed, scheduling unavailable")
                self.apscheduler = None
        elif self.scheduler_type == "kubernetes":
            logger.info("using kubernetes cronjob scheduler")
        else:
            logger.warning(f"unknown scheduler type: {self.scheduler_type}")

    def create_schedule(
        self,
        model_id: UUID,
        cron_expression: str,
        enabled: bool = True
    ) -> str:
        '''
        create a schedule for model execution
        cron_expression format: "minute hour day month day_of_week"
        returns schedule id
        '''
        if self.scheduler_type == "apscheduler" and self.apscheduler:
            return self._create_apscheduler_job(model_id, cron_expression, enabled)
        elif self.scheduler_type == "kubernetes":
            return self._create_k8s_cronjob(model_id, cron_expression, enabled)
        else:
            raise ValueError("scheduler not available")

    def _create_apscheduler_job(
        self,
        model_id: UUID,
        cron_expression: str,
        enabled: bool
    ) -> str:
        '''
        create apscheduler job
        '''
        if not self.apscheduler:
            raise ValueError("apscheduler not initialized")

        # parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("cron expression must have 5 parts: minute hour day month day_of_week")

        minute, hour, day, month, day_of_week = parts

        # create job function
        def execute_scheduled_model():
            try:
                logger.info(f"executing scheduled model {model_id}")
                from uuid import UUID
                self.orchestrator.execute_model(UUID(str(model_id)))
            except Exception as e:
                logger.error(f"scheduled model execution failed: {e}")

        # add job
        job_id = f"model_{model_id}"
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )

        if enabled:
            self.apscheduler.add_job(
                execute_scheduled_model,
                trigger=trigger,
                id=job_id,
                replace_existing=True
            )
            logger.info(f"created apscheduler job {job_id} with cron {cron_expression}")
        else:
            logger.info(f"schedule created but disabled for model {model_id}")

        return job_id

    def _create_k8s_cronjob(
        self,
        model_id: UUID,
        cron_expression: str,
        enabled: bool
    ) -> str:
        '''
        create kubernetes cronjob
        '''
        try:
            from kubernetes import client, config
            from kubernetes.client.rest import ApiException
        except ImportError:
            raise ValueError("kubernetes library not installed")

        try:
            config.load_incluster_config()
        except:
            try:
                config.load_kube_config()
            except:
                raise ValueError("kubernetes config not available")

        # parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("cron expression must have 5 parts: minute hour day month day_of_week")

        # kubernetes cron format is slightly different
        # convert: minute hour day month day_of_week -> minute hour day month day_of_week
        k8s_cron = f"{parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]}"

        job_name = f"model-schedule-{model_id}"
        namespace = os.getenv("KUBERNETES_NAMESPACE", "default")

        # create cronjob manifest
        cronjob_manifest = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {
                "name": job_name,
                "namespace": namespace
            },
            "spec": {
                "schedule": k8s_cron,
                "suspend": not enabled,
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [{
                                    "name": "model-executor",
                                    "image": "openuba-backend:latest",
                                    "command": ["python", "-c", f"""
import os
os.environ['MODEL_ID'] = '{model_id}'
from core.services.model_orchestrator import ModelOrchestrator
orchestrator = ModelOrchestrator()
orchestrator.execute_model('{model_id}')
                                    """],
                                    "env": [
                                        {"name": "DATABASE_URL", "valueFrom": {"secretKeyRef": {"name": "backend-secret", "key": "database-url"}}},
                                        {"name": "MODEL_ID", "value": str(model_id)},
                                        {"name": "EXECUTION_MODE", "value": "kubernetes"}
                                    ]
                                }],
                                "restartPolicy": "OnFailure"
                            }
                        }
                    }
                }
            }
        }

        batch_api = client.BatchV1Api()
        try:
            cronjob = batch_api.create_namespaced_cron_job(
                body=cronjob_manifest,
                namespace=namespace
            )
            logger.info(f"created kubernetes cronjob {job_name} with schedule {k8s_cron}")
            return job_name
        except ApiException as e:
            logger.error(f"failed to create kubernetes cronjob: {e}")
            raise

    def delete_schedule(self, schedule_id: str) -> None:
        '''
        delete a schedule
        '''
        if self.scheduler_type == "apscheduler" and self.apscheduler:
            try:
                self.apscheduler.remove_job(schedule_id)
                logger.info(f"removed apscheduler job {schedule_id}")
            except Exception as e:
                logger.warning(f"failed to remove apscheduler job: {e}")
        elif self.scheduler_type == "kubernetes":
            try:
                from kubernetes import client, config
                from kubernetes.client.rest import ApiException

                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()

                batch_api = client.BatchV1Api()
                namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
                batch_api.delete_namespaced_cron_job(
                    name=schedule_id,
                    namespace=namespace
                )
                logger.info(f"deleted kubernetes cronjob {schedule_id}")
            except Exception as e:
                logger.error(f"failed to delete kubernetes cronjob: {e}")
                raise

    def list_schedules(self) -> list[Dict[str, Any]]:
        '''
        list all active schedules
        '''
        schedules = []
        if self.scheduler_type == "apscheduler" and self.apscheduler:
            jobs = self.apscheduler.get_jobs()
            for job in jobs:
                schedules.append({
                    "id": job.id,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        elif self.scheduler_type == "kubernetes":
            try:
                from kubernetes import client, config

                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()

                batch_api = client.BatchV1Api()
                namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
                cronjobs = batch_api.list_namespaced_cron_job(namespace=namespace)
                for cj in cronjobs.items:
                    if cj.metadata.name.startswith("model-schedule-"):
                        schedules.append({
                            "id": cj.metadata.name,
                            "schedule": cj.spec.schedule,
                            "suspended": cj.spec.suspend if hasattr(cj.spec, "suspend") else False
                        })
            except Exception as e:
                logger.error(f"failed to list kubernetes cronjobs: {e}")

        return schedules

    def shutdown(self) -> None:
        '''
        shutdown scheduler
        '''
        if self.apscheduler:
            self.apscheduler.shutdown()
            logger.info("apscheduler shut down")

