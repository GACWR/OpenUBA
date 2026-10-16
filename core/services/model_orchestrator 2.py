'''
Copyright 2019-Present The OpenUBA Platform Authors
model execution orchestrator for containerized execution
'''

import os
import logging
import json
import time
import threading
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from pathlib import Path

from core.db import get_db_context
from core.repositories.model_repository import ModelRepository
from core.db.models import ExecutionLog, ModelRun, ModelVersion, ModelArtifact
from core.services.model_installer import ModelInstaller

logger = logging.getLogger(__name__)


class ModelOrchestrator:
    '''
    orchestrates model execution in containers
    supports both docker and kubernetes
    '''

    def __init__(self):
        self.execution_mode = os.getenv("EXECUTION_MODE", "docker")  # docker or kubernetes
        self.model_storage_path = Path(
            os.getenv("MODEL_STORAGE_PATH", "core/model_library")
        )
        self.model_installer = ModelInstaller()

    def _create_run(
        self,
        model_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
        run_type: str = "infer",
        version_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None
    ) -> Tuple[UUID, UUID]:
        '''
        create ModelRun and ExecutionLog records in the database
        returns (run_id, execution_id)
        '''
        with get_db_context() as db:
            repo = ModelRepository(db)
            model = repo.get_by_id(model_id)
            if not model:
                raise ValueError(f"model not found: {model_id}")

            # get model version (use default if not specified)
            if version_id:
                model_version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
            elif model.default_version_id:
                model_version = db.query(ModelVersion).filter(ModelVersion.id == model.default_version_id).first()
            else:
                # get latest version
                model_version = db.query(ModelVersion).filter(
                    ModelVersion.model_id == model_id
                ).order_by(ModelVersion.installed_at.desc()).first()

            if not model_version:
                raise ValueError(f"no model version found for model {model_id}")

            # verify model files before execution
            if not self.model_installer.verify_installed_model(model_id):
                raise ValueError("model verification failed")

            # for inference, get artifact if specified or use latest
            artifact = None
            if run_type == "infer" and artifact_id:
                artifact = db.query(ModelArtifact).filter(ModelArtifact.id == artifact_id).first()
            elif run_type == "infer" and not artifact_id:
                artifact = db.query(ModelArtifact).filter(
                    ModelArtifact.model_version_id == model_version.id,
                    ModelArtifact.kind == "checkpoint"
                ).order_by(ModelArtifact.created_at.desc()).first()

            # create model run
            data_loader_type = None
            data_loader_context = None
            if input_data:
                data_loader_type = input_data.get("data_source") or input_data.get("type")
                data_loader_context = input_data

            model_run = ModelRun(
                model_version_id=model_version.id,
                artifact_id=artifact.id if artifact else None,
                run_type=run_type,
                status="pending",
                data_loader_type=data_loader_type,
                data_loader_context=data_loader_context,
                params=input_data.get("params") if input_data else None
            )
            db.add(model_run)
            db.commit()
            db.refresh(model_run)
            run_id = model_run.id

            # also create execution log for backward compatibility
            execution_log = ExecutionLog(
                model_id=model_id,
                status="pending"
            )
            db.add(execution_log)
            db.commit()
            db.refresh(execution_log)
            execution_id = execution_log.id

        return run_id, execution_id

    def _execute_and_finalize(
        self,
        model_id: UUID,
        run_id: UUID,
        execution_id: UUID,
        input_data: Optional[Dict[str, Any]],
        run_type: str
    ) -> None:
        '''
        execute model and update DB records
        designed to run in a background thread
        '''
        try:
            # mark as dispatched
            with get_db_context() as db:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                run.status = "dispatched"
                run.started_at = datetime.utcnow()

                log = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
                log.status = "running"
                log.started_at = datetime.utcnow()
                db.commit()

            # execute based on mode
            if self.execution_mode == "kubernetes":
                result = self._execute_kubernetes(model_id, execution_id, input_data, run_type, run_id)
            else:
                result = self._execute_docker(model_id, execution_id, input_data, run_type, run_id)

            # store anomalies from result
            # in K8s mode, the runner persists anomalies directly to the DB,
            # so we only create anomalies from the result if running in Docker mode
            anomalies_created = 0
            if self.execution_mode != "kubernetes" and result and result.get("anomalies"):
                from core.repositories.anomaly_repository import AnomalyRepository

                with get_db_context() as db:
                    anomaly_repo = AnomalyRepository(db)
                    for anomaly_data in result["anomalies"]:
                        try:
                            entity_id = str(anomaly_data.get("entity_id", "unknown"))
                            risk_score = float(anomaly_data.get("risk_score")) if anomaly_data.get("risk_score") is not None else None

                            anomaly = anomaly_repo.create(
                                model_id=model_id,
                                entity_id=entity_id,
                                entity_type=anomaly_data.get("entity_type", "user"),
                                risk_score=risk_score,
                                anomaly_type=anomaly_data.get("anomaly_type"),
                                details=anomaly_data.get("details"),
                                timestamp=datetime.utcnow(),
                                run_id=run_id
                            )
                            anomalies_created += 1
                        except Exception as e:
                            logger.warning(f"failed to create anomaly: {e}")
                            import traceback
                            logger.warning(traceback.format_exc())
                    db.commit()

            # evaluate flow rules after inference
            # NO hardcoded pre-filtering — the rule engine's flow graph conditions
            # decide what triggers. we just identify anomalies from this run.
            # fetched in batches to keep memory bounded for large runs (195k+).
            if run_type == "infer":
                try:
                    from core.services.rule_engine import RuleEngine
                    from sqlalchemy import text as sa_text

                    rule_engine = RuleEngine()
                    total_alerts_fired = 0
                    total_anomalies_evaluated = 0
                    alert_budget = rule_engine.MAX_ALERTS_PER_RUN
                    batch_size = 5000

                    if self.execution_mode == "kubernetes":
                        # in K8s mode, runner already persisted anomalies to the DB
                        # tagged with run_id. fetch in batches to bound memory.
                        offset = 0
                        while alert_budget > 0:
                            with get_db_context() as db:
                                rows = db.execute(
                                    sa_text(
                                        "SELECT entity_id, entity_type, risk_score, "
                                        "anomaly_type, details "
                                        "FROM anomalies WHERE run_id = :run_id "
                                        "ORDER BY risk_score DESC "
                                        "LIMIT :lim OFFSET :off"
                                    ),
                                    {"run_id": str(run_id), "lim": batch_size, "off": offset}
                                ).fetchall()

                            if not rows:
                                break

                            batch = []
                            for row in rows:
                                batch.append({
                                    "entity_id": row[0],
                                    "entity_type": row[1],
                                    "risk_score": float(row[2]) if row[2] else 0,
                                    "anomaly_type": row[3],
                                    "details": row[4],
                                    "model_id": str(model_id),
                                })

                            total_anomalies_evaluated += len(batch)

                            with get_db_context() as rule_db:
                                fired = rule_engine.evaluate_after_inference(
                                    model_id, batch, rule_db,
                                    max_alerts=alert_budget
                                )
                            total_alerts_fired += fired
                            alert_budget -= fired

                            offset += batch_size

                            # if we got fewer rows than batch_size, we're done
                            if len(rows) < batch_size:
                                break

                        anomalies_created = total_anomalies_evaluated
                    else:
                        # Docker mode: anomalies come from the result dict
                        all_anomalies = result.get("anomalies", []) if result else []
                        # process in batches for memory safety
                        for i in range(0, len(all_anomalies), batch_size):
                            if alert_budget <= 0:
                                break
                            batch = all_anomalies[i:i + batch_size]
                            total_anomalies_evaluated += len(batch)
                            with get_db_context() as rule_db:
                                fired = rule_engine.evaluate_after_inference(
                                    model_id, batch, rule_db,
                                    max_alerts=alert_budget
                                )
                            total_alerts_fired += fired
                            alert_budget -= fired

                    if total_alerts_fired > 0:
                        logger.info(
                            f"rule evaluation: {total_alerts_fired} alert(s) fired "
                            f"from {total_anomalies_evaluated} anomalies"
                        )
                    elif total_anomalies_evaluated > 0:
                        logger.info(
                            f"rule evaluation: 0 alerts fired "
                            f"from {total_anomalies_evaluated} anomalies"
                        )
                    else:
                        logger.info("rule evaluation: no anomalies from this run")
                except Exception as e:
                    logger.warning(f"rule evaluation failed (non-fatal): {e}")
                    import traceback
                    logger.warning(traceback.format_exc())

            # build a lightweight summary (strip bulky anomalies list)
            result_summary = {
                k: v for k, v in (result or {}).items()
                if k != "anomalies"
            }
            result_summary["anomalies_created"] = anomalies_created

            # update model run and execution log
            with get_db_context() as db:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                run.status = "succeeded"
                run.finished_at = datetime.utcnow()
                run.result_summary = result_summary

                log = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
                log.status = "completed"
                log.completed_at = datetime.utcnow()
                log.output_summary = result_summary
                if result and result.get("execution_time"):
                    log.execution_time_seconds = result["execution_time"]

                # after successful training, update model version status
                if run_type == "train" and run:
                    artifact = db.query(ModelArtifact).filter(
                        ModelArtifact.model_version_id == run.model_version_id,
                        ModelArtifact.kind == "checkpoint"
                    ).order_by(ModelArtifact.created_at.desc()).first()
                    if artifact:
                        model_version = db.query(ModelVersion).filter(
                            ModelVersion.id == run.model_version_id
                        ).first()
                        if model_version and model_version.status != "trained":
                            model_version.status = "trained"
                            model_version.updated_at = datetime.utcnow()
                        if not run.artifact_id:
                            run.artifact_id = artifact.id

                db.commit()

            logger.info(f"model execution completed: run_id={run_id}, execution_id={execution_id}")

        except Exception as e:
            with get_db_context() as db:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                run.status = "failed"
                run.finished_at = datetime.utcnow()
                run.error_message = str(e)

                log = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
                log.status = "failed"
                log.completed_at = datetime.utcnow()
                log.error_message = str(e)
                import traceback
                log.error_traceback = traceback.format_exc()
                db.commit()
            logger.error(f"model execution failed: {e}")

    def execute_model_background(
        self,
        model_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
        run_type: str = "infer",
        version_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None
    ) -> UUID:
        '''
        create run records and dispatch execution to a background thread
        returns run_id immediately
        '''
        logger.info(f"dispatching model {model_id}, run_type={run_type}")

        run_id, execution_id = self._create_run(
            model_id, input_data, run_type, version_id, artifact_id
        )

        thread = threading.Thread(
            target=self._execute_and_finalize,
            args=(model_id, run_id, execution_id, input_data, run_type),
            daemon=True,
            name=f"model-{run_type}-{run_id}"
        )
        thread.start()

        logger.info(f"model {run_type} dispatched: run_id={run_id}")
        return run_id

    def execute_model(
        self,
        model_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
        run_type: str = "infer",
        version_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None
    ) -> UUID:
        '''
        execute a model synchronously (blocks until done)
        kept for backward compatibility / testing
        '''
        logger.info(f"executing model {model_id}, run_type={run_type} (synchronous)")

        run_id, execution_id = self._create_run(
            model_id, input_data, run_type, version_id, artifact_id
        )

        self._execute_and_finalize(model_id, run_id, execution_id, input_data, run_type)
        return run_id

    def _execute_docker(
        self,
        model_id: UUID,
        execution_id: UUID,
        input_data: Optional[Dict[str, Any]],
        run_type: str = "infer",
        run_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        '''
        execute model in docker container
        '''
        try:
            import docker
            client = docker.from_env()
        except ImportError:
            raise ValueError("docker python library not installed")
        except Exception as e:
            raise ValueError(f"docker not available: {e}")

        with get_db_context() as db:
            repo = ModelRepository(db)
            model = repo.get_by_id(model_id)
            model_name = model.name
            model_slug = model.slug or model.name
            model_runtime = model.runtime
            model_path = self.model_storage_path / model.name

            # get model version for slug/version info
            model_version_str = model.version or "1.0.0"
            if run_id:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                if run and run.model_version:
                    model_version_str = run.model_version.version or model_version_str

            # for inference, get artifact path if one exists
            artifact_path_env = None
            if run_type == "infer" and run_id:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                if run and run.artifact_id:
                    artifact = db.query(ModelArtifact).filter(ModelArtifact.id == run.artifact_id).first()
                    if artifact and artifact.path:
                        artifact_path_env = artifact.path
                elif run:
                    # no artifact_id on run, try latest checkpoint for this version
                    latest_artifact = db.query(ModelArtifact).filter(
                        ModelArtifact.model_version_id == run.model_version_id,
                        ModelArtifact.kind == "checkpoint"
                    ).order_by(ModelArtifact.created_at.desc()).first()
                    if latest_artifact and latest_artifact.path:
                        artifact_path_env = latest_artifact.path

        # prepare input data - pass as env var or file
        input_file = None
        input_data_json = None
        if input_data:
            # try env var first (simpler for k8s)
            input_data_json = json.dumps(input_data)
            # also create file as fallback
            import tempfile
            input_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(input_data, input_file)
            input_file.close()

        try:
            # run container with resource limits
            # get project root (assuming we are in core/services/model_orchestrator.py)
            project_root = Path(__file__).resolve().parent.parent.parent
            core_path = project_root / "core"
            runner_path = project_root / "docker" / "model-runner" / "runner.py"

            # adjust env vars for docker networking (localhost -> host.docker.internal)
            db_url = os.getenv("DATABASE_URL", "postgresql://openuba:openuba@postgres:5432/openuba")
            es_url = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")

            if "localhost" in db_url:
                db_url = db_url.replace("localhost", "host.docker.internal")
            if "127.0.0.1" in db_url:
                db_url = db_url.replace("127.0.0.1", "host.docker.internal")

            if "localhost" in es_url:
                es_url = es_url.replace("localhost", "host.docker.internal")
            if "127.0.0.1" in es_url:
                es_url = es_url.replace("127.0.0.1", "host.docker.internal")

            # Determine Docker Image based on Runtime
            runtime = model_runtime or "python-base"
            image_tag = "base"
            if runtime == "python-base":
                image_tag = "base"
            else:
                image_tag = runtime
            image_name = f"openuba-model-runner:{image_tag}"

            # Ensure saved_models directory exists for artifact persistence
            saved_models_path = project_root / "core" / "storage" / "saved_models"
            saved_models_path.mkdir(parents=True, exist_ok=True)

            # Build environment variables
            env_vars = {
                "MODEL_ID": str(model_id),
                "EXECUTION_ID": str(execution_id),
                "RUN_ID": str(run_id) if run_id else None,
                "RUN_TYPE": run_type,
                "INPUT_DATA": input_data_json if input_data_json else None,
                "INPUT_DATA_FILE": input_file.name if input_file else None,
                "MODEL_PATH": "/model",
                "MODEL_SLUG": model_slug,
                "MODEL_VERSION": model_version_str,
                "MODEL_RUNTIME": runtime,
                "SAVED_MODELS_PATH": "/opt/openuba/saved_models",
                "DATABASE_URL": db_url,
                "SPARK_MASTER_URL": os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077"),
                "ELASTICSEARCH_HOST": es_url
            }

            # For inference, pass artifact path so runner can load trained model
            if artifact_path_env:
                env_vars["ARTIFACT_PATH"] = artifact_path_env

            container = client.containers.run(
                image=image_name,
                volumes={
                    str(model_path.resolve()): {"bind": "/model", "mode": "ro"},
                    str(core_path): {"bind": "/app/core", "mode": "ro"},
                    str(runner_path): {"bind": "/app/runner.py", "mode": "ro"},
                    str(saved_models_path.resolve()): {"bind": "/opt/openuba/saved_models", "mode": "rw"},
                    "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}
                },
                environment=env_vars,
                detach=False,
                remove=True,
                network_mode="bridge",
                mem_limit="2g",  # 2GB memory limit
                cpu_quota=200000,  # 2 CPU cores (in microseconds per second)
                cpu_period=100000,
                user="1000:1000",  # non-root user
                security_opt=["no-new-privileges:true"]
            )

            # parse output
            output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
            try:
                result = json.loads(output)
            except json.JSONDecodeError:
                result = {"output": output}

            # update container id in log
            with get_db_context() as db:
                log = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
                log.container_id = container.id if hasattr(container, "id") else None
                db.commit()

            return result

        finally:
            if input_file:
                os.unlink(input_file.name)

    def _execute_kubernetes(
        self,
        model_id: UUID,
        execution_id: UUID,
        input_data: Optional[Dict[str, Any]],
        run_type: str = "infer",
        run_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        '''
        execute model using JIT Operator (UBAInference CRD)
        '''
        try:
            from kubernetes import client, config
            from kubernetes.client.rest import ApiException
        except ImportError:
            raise ValueError("kubernetes python library not installed")

        try:
            config.load_incluster_config()
        except:
            try:
                config.load_kube_config()
            except:
                raise ValueError("kubernetes config not available")

        with get_db_context() as db:
            repo = ModelRepository(db)
            model = repo.get_by_id(model_id)
            model_name = model.name
            model_slug = model.slug or model.name
            model_runtime = model.runtime
            model_version_str = model.version or "1.0.0"

            # get version from run if available
            if run_id:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                if run and run.model_version:
                    model_version_str = run.model_version.version or model_version_str

            # for inference, resolve artifact path
            artifact_path_env = None
            if run_type == "infer" and run_id:
                run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                if run and run.artifact_id:
                    artifact = db.query(ModelArtifact).filter(ModelArtifact.id == run.artifact_id).first()
                    if artifact and artifact.path:
                        artifact_path_env = artifact.path
                elif run:
                    latest_artifact = db.query(ModelArtifact).filter(
                        ModelArtifact.model_version_id == run.model_version_id,
                        ModelArtifact.kind == "checkpoint"
                    ).order_by(ModelArtifact.created_at.desc()).first()
                    if latest_artifact and latest_artifact.path:
                        artifact_path_env = latest_artifact.path

        # Paths logic
        # Backend mounts PVC at self.model_storage_path (e.g. /app/core/model_library)
        # Runner mounts PVC at /model

        # 1. Prepare IO directories
        # Use hidden directory for temporary inference artifacts to keep root clean
        project_root = Path(__file__).parent.parent.parent
        inference_dir = project_root / ".openuba" / "inference" / str(execution_id)
        inference_dir.mkdir(parents=True, exist_ok=True)

        input_filename = "input.json"
        output_filename = "output.json"

        local_input_path = inference_dir / input_filename
        local_output_path = inference_dir / output_filename

        # Container paths (what the runner sees, mounted at /system)
        runner_input_path = f"/system/inference/{execution_id}/{input_filename}"
        runner_output_path = f"/system/inference/{execution_id}/{output_filename}"

        # 2. Write Input
        if input_data:
            with open(local_input_path, "w") as f:
                json.dump(input_data, f)
        else:
            # Create empty input if none
            with open(local_input_path, "w") as f:
                json.dump({}, f)

        # 3. Create CRD (Inference or Training)
        crd_name = f"{'inf' if run_type == 'infer' else 'train'}-{execution_id}"
        namespace = os.getenv("KUBERNETES_NAMESPACE", "openuba")
        runtime = model_runtime or "python-base"

        api = client.CustomObjectsApi()
        plural = ""

        if run_type == "infer":
            plural = "ubainferences"
            crd_manifest = {
                "apiVersion": "openuba.io/v1alpha1",
                "kind": "UBAInference",
                "metadata": {"name": crd_name, "namespace": namespace},
                "spec": {
                    "modelRef": model_name,
                    "runtime": runtime,
                    "inputPath": runner_input_path,
                    "outputPath": runner_output_path,
                    "runId": str(run_id) if run_id else "",
                    "executionId": str(execution_id) if execution_id else "",
                    "modelSlug": model_slug,
                    "modelVersion": model_version_str,
                    "artifactPath": artifact_path_env or ""
                }
            }
        else: # train
            plural = "ubatrainings"
            crd_manifest = {
                "apiVersion": "openuba.io/v1alpha1",
                "kind": "UBATraining",
                "metadata": {"name": crd_name, "namespace": namespace},
                "spec": {
                    "modelRef": model_name,
                    "runtime": runtime,
                    "configPath": runner_input_path,
                    "outputPath": runner_output_path,
                    "runId": str(run_id) if run_id else "",
                    "executionId": str(execution_id) if execution_id else "",
                    "modelSlug": model_slug,
                    "modelVersion": model_version_str
                }
            }

        try:
            api.create_namespaced_custom_object(
                group="openuba.io",
                version="v1alpha1",
                namespace=namespace,
                plural=plural,
                body=crd_manifest
            )

            # Update status to running
            with get_db_context() as db:
                if run_id:
                    run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
                    run.k8s_job_name = crd_name
                    run.status = "running"
                    db.commit()

            # Poll for completion — this runs in a background thread so
            # it won't block the uvicorn event loop
            max_wait = 3600  # 1 hour
            wait_time = 0

            while wait_time < max_wait:
                time.sleep(5)
                wait_time += 5

                resource = api.get_namespaced_custom_object(
                    group="openuba.io",
                    version="v1alpha1",
                    namespace=namespace,
                    plural=plural,
                    name=crd_name
                )

                status = resource.get("status", {})
                phase = status.get("phase")

                if phase == "Succeeded":
                    # Read Output
                    if local_output_path.exists():
                        with open(local_output_path, "r") as f:
                            try:
                                return json.load(f)
                            except json.JSONDecodeError:
                                return {"error": "Invalid JSON output", "raw": f.read()}
                    else:
                        return {"status": "success", "message": "Job completed"}

                elif phase == "Failed":
                    raise Exception(f"{run_type} failed: {status.get('message')}")

            raise Exception("Execution timed out")

        except ApiException as e:
            raise Exception(f"Kubernetes API error: {e}")
        except Exception as e:
            raise Exception(f"Execution failed: {e}")
