#!/usr/bin/env python3
'''
Copyright 2019-Present The OpenUBA Platform Authors
model runner script for containerized execution
'''

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
import pandas as pd

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ModelLogHandler(logging.Handler):
    '''
    custom logging handler that captures log records and flushes them
    to the model_logs postgres table in batches.
    '''
    def __init__(self, run_id, db_url):
        super().__init__()
        self.run_id = str(run_id)
        self.db_url = db_url
        self.buffer = []
        self.buffer_size = 10

    def emit(self, record):
        from datetime import datetime
        self.buffer.append({
            "model_run_id": self.run_id,
            "level": record.levelname.lower(),
            "message": self.format(record),
            "logger_name": record.name,
            "created_at": datetime.utcfromtimestamp(record.created),
        })
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "INSERT INTO model_logs (model_run_id, level, message, logger_name, created_at) "
                        "VALUES (:model_run_id, :level, :message, :logger_name, :created_at)"
                    ),
                    self.buffer
                )
                conn.commit()
            self.buffer.clear()
            engine.dispose()
        except Exception as e:
            # don't recurse — just print to stderr
            print(f"[ModelLogHandler] failed to flush logs to DB: {e}", file=sys.stderr)

    def close(self):
        self.flush()
        super().close()


class MetricReporter:
    '''
    reports training metrics back to the OpenUBA platform API
    posts metrics to the internal /api/v1/internal/metrics/{job_id} endpoint
    so the frontend can display live training progress via SSE
    '''
    def __init__(self, job_id, api_url=None):
        self.job_id = str(job_id)
        self.api_url = (api_url or os.environ.get(
            "OPENUBA_API_URL", "http://openuba-backend:8000"
        )).rstrip("/")
        self._session = None

    def _get_session(self):
        if self._session is None:
            import requests as req
            self._session = req.Session()
        return self._session

    def report(self, metric_name, metric_value, epoch=None, step=None):
        '''report a single metric to the platform'''
        try:
            session = self._get_session()
            payload = {
                "metric_name": metric_name,
                "metric_value": float(metric_value),
            }
            if epoch is not None:
                payload["epoch"] = int(epoch)
            if step is not None:
                payload["step"] = int(step)

            url = f"{self.api_url}/api/v1/internal/metrics/{self.job_id}"
            resp = session.post(url, json=payload, timeout=5)
            if resp.status_code != 201:
                logger.warning(f"metric report failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.warning(f"[MetricReporter] failed to report metric: {e}")

    def report_batch(self, metrics):
        '''report multiple metrics at once: list of (name, value, epoch, step) tuples'''
        for item in metrics:
            if len(item) == 4:
                name, value, epoch, step = item
            elif len(item) == 2:
                name, value = item
                epoch, step = None, None
            else:
                continue
            self.report(name, value, epoch=epoch, step=step)

    def report_progress(self, progress, epoch_current=None, epoch_total=None, loss=None):
        '''report job progress to the platform via PATCH'''
        try:
            session = self._get_session()
            payload = {"progress": int(progress)}
            if epoch_current is not None:
                payload["epoch_current"] = int(epoch_current)
            if epoch_total is not None:
                payload["epoch_total"] = int(epoch_total)
            if loss is not None:
                payload["loss"] = float(loss)

            url = f"{self.api_url}/api/v1/jobs/{self.job_id}"
            session.patch(url, json=payload, timeout=5)
        except Exception as e:
            logger.warning(f"[MetricReporter] failed to report progress: {e}")


def hash_file(file_path: Path) -> str:
    '''
    compute sha256 hash of a file
    '''
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_model_files(model_path: Path, expected_hashes: dict) -> bool:
    '''
    verify model files against expected hashes
    '''
    if not expected_hashes:
        logger.warning("no expected hashes provided, skipping verification")
        return True

    for filename, expected_hash in expected_hashes.items():
        file_path = model_path / filename
        if not file_path.exists():
            logger.error(f"model file not found: {filename}")
            return False

        actual_hash = hash_file(file_path)
        if actual_hash != expected_hash:
            logger.error(
                f"hash mismatch for {filename}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
            return False

    return True


def load_model(model_path: Path):
    '''
    load and import model
    '''
    # add model path to sys.path
    sys.path.insert(0, str(model_path))

    try:
        # import model module
        import MODEL
        return MODEL
    except ImportError as e:
        logger.error(f"failed to import model: {e}")
        raise
    finally:
        # remove from path after import
        if str(model_path) in sys.path:
            sys.path.remove(str(model_path))


def execute_model(model_path: Path, input_data: dict = None, run_type: str = "infer") -> dict:
    '''
    execute model and return results
    supports both v1 (execute) and v2 (train/infer) interfaces
    '''
    logger.info(f"executing model from {model_path}, run_type={run_type}")

    # load model
    model_module = load_model(model_path)

    # determine interface version
    has_execute = hasattr(model_module, "execute")
    has_model_class = hasattr(model_module, "Model")
    
    # try v2 interface first (preferred)
    if has_model_class:
        try:
            ModelCls = getattr(model_module, "Model")
            model_instance = ModelCls()
            
            if run_type == "train":
                if hasattr(model_instance, "train"):
                    # create training context
                    class TrainingContext:
                        def __init__(self, input_data):
                            self.params = input_data or {}
                            self.logger = logger
                            # load data if specified
                            if input_data:
                                self.df = _load_data_for_model(input_data)
                            else:
                                self.df = None

                    ctx = TrainingContext(input_data)
                    result = model_instance.train(ctx)

                    # serialize trained model artifact to persistent storage
                    artifact_info = _save_trained_artifact(model_instance)

                    train_result = {"status": "success", "training_result": result}
                    if artifact_info:
                        train_result["artifact_info"] = artifact_info
                    return train_result
                else:
                    logger.warning("model does not support training, skipping")
                    return {"status": "skipped", "message": "model does not support training"}

            elif run_type == "infer":
                if hasattr(model_instance, "infer"):
                    # load trained artifact if available
                    _load_trained_artifact(model_instance)

                    # create inference context
                    class InferenceContext:
                        def __init__(self, input_data):
                            self.params = input_data or {}
                            self.logger = logger
                            # load data if specified
                            if input_data:
                                self.df = _load_data_for_model(input_data)
                            else:
                                self.df = None

                    ctx = InferenceContext(input_data)
                    result_df = model_instance.infer(ctx)

                    # convert dataframe to anomalies format
                    if isinstance(result_df, pd.DataFrame) and len(result_df) > 0:
                        logger.info(f"model returned {len(result_df)} result rows, converting to anomalies...")
                        anomalies = result_df.to_dict("records")
                        anomaly_count = len(anomalies)
                        high_risk = sum(1 for a in anomalies if float(a.get("risk_score", 0)) >= 50)
                        logger.info(f"inference complete: {anomaly_count} results, {high_risk} high-risk anomalies")
                        return {
                            "anomalies": anomalies,
                            "status": "success",
                            "anomaly_count": anomaly_count
                        }
                    else:
                        logger.info("inference complete: 0 anomalies detected")
                        return {
                            "anomalies": [],
                            "status": "success",
                            "anomaly_count": 0
                        }
                else:
                    logger.warning("model does not have infer method, falling back to execute")
                    # fall through to v1 interface
            
            # if we get here, v2 interface didn't work, try v1
            if has_execute:
                logger.info("using v1 execute interface")
                if input_data:
                    result = model_module.execute(input_data)
                else:
                    result = model_module.execute()
                return _normalize_v1_result(result)
        
        except (ImportError, AttributeError) as e:
            logger.warning(f"v2 interface unavailable: {e}, trying v1 interface")
            # fall through to v1 only for interface-level errors
    
    # v1 interface (backward compatibility)
    if has_execute:
        logger.info("using v1 execute interface")
        try:
            if input_data:
                result = model_module.execute(input_data)
            else:
                result = model_module.execute()
            return _normalize_v1_result(result)
        except Exception as e:
            logger.error(f"model execution failed: {e}")
            raise
    else:
        raise ValueError("model must have either Model class (v2) or execute() function (v1)")


def _load_data_for_model(input_data: dict):
    '''
    helper to load data based on input_data configuration.
    uses direct implementations (no core.* imports since runner container
    does not have the core package).
    returns pandas dataframe.
    '''
    import pandas as pd
    import requests

    if not input_data:
        return pd.DataFrame()

    data_source = input_data.get("data_source") or input_data.get("type")

    try:
        if data_source == "elasticsearch":
            query = input_data.get("query", {"match_all": {}})
            host = input_data.get("host", os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200"))
            index_name = input_data.get("index_name") or input_data.get("index")
            if index_name:
                url = f"{host.rstrip('/')}/{index_name}/_search"
            else:
                url = host
            payload = {"query": query, "size": input_data.get("size", 10000)}
            logger.info(f"querying elasticsearch: {url}")
            resp = requests.get(url, json=payload, headers={"content-type": "application/json"}, timeout=60)
            if resp.status_code == 200:
                hits = resp.json().get("hits", {}).get("hits", [])
                docs = [h["_source"] for h in hits]
                df = pd.DataFrame(docs)
                for col in df.columns:
                    converted = pd.to_numeric(df[col], errors="coerce")
                    if converted.notna().mean() > 0.5:
                        df[col] = converted
                logger.info(f"loaded {len(df)} rows from elasticsearch index {index_name or 'default'}")
                return df
            else:
                raise ValueError(f"elasticsearch query failed ({resp.status_code}): {resp.text[:500]}")

        elif data_source == "spark":
            table_name = input_data.get("table_name")
            if not table_name:
                raise ValueError("table_name required for spark")

            # spark tables are external CSVs on datasets PVC.
            # parse table name to find the data directory.
            # convention: table_name = "{dataset}_{log_type}" e.g. "toy_1_proxy"
            datasets_path = os.getenv("DATASETS_PATH", "/app/test_datasets")

            last_underscore = table_name.rfind("_")
            if last_underscore > 0:
                dataset = table_name[:last_underscore]
                log_type = table_name[last_underscore + 1:]
            else:
                raise ValueError(f"cannot parse table name '{table_name}' — expected format: dataset_logtype")

            data_dir = os.path.join(datasets_path, dataset, log_type)
            if not os.path.isdir(data_dir):
                raise ValueError(f"data directory not found: {data_dir}")

            # find data files
            data_files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
            if not data_files:
                raise ValueError(f"no data files found in {data_dir}")

            # determine CSV options based on log type (matches data_ingestion.py)
            if log_type in ("ssh", "dns", "dhcp"):
                sep = "\t"
                has_header = False
                encoding = "UTF-8"
            elif log_type in ("proxy", "bluecoat"):
                sep = " "
                has_header = True
                encoding = "ISO-8859-1"
            else:
                sep = " "
                has_header = True
                encoding = "UTF-8"

            # use pyspark local mode to read the data
            from pyspark.sql import SparkSession
            logger.info(f"creating local spark session to read table '{table_name}' from {data_dir}")
            spark = SparkSession.builder \
                .master("local[*]") \
                .appName("model-runner") \
                .config("spark.driver.memory", "512m") \
                .config("spark.ui.enabled", "false") \
                .getOrCreate()

            try:
                spark_df = spark.read \
                    .option("sep", sep) \
                    .option("header", str(has_header).lower()) \
                    .option("inferSchema", "true") \
                    .option("encoding", encoding) \
                    .csv(data_dir)
                row_count = spark_df.count()
                df = spark_df.toPandas()
                # coerce numeric columns (errors="coerce" converts bad values to NaN)
                for col in df.columns:
                    converted = pd.to_numeric(df[col], errors="coerce")
                    # only keep as numeric if >50% of values are non-NaN
                    if converted.notna().mean() > 0.5:
                        df[col] = converted
                logger.info(f"loaded {row_count} rows from spark table '{table_name}' (dir: {data_dir})")
                return df
            finally:
                spark.stop()

        elif data_source == "local_csv":
            file_path = input_data.get("file_path")
            file_name = input_data.get("file_name")
            if not file_path or not file_name:
                raise ValueError("file_path and file_name required for local_csv")
            full_path = os.path.join(file_path, file_name)
            df = pd.read_csv(full_path, sep=input_data.get("sep", ","), header=input_data.get("header", 0))
            logger.info(f"loaded {len(df)} rows from {full_path}")
            return df

        elif data_source:
            raise ValueError(f"unknown data source: {data_source}")
        else:
            return pd.DataFrame()

    except Exception as e:
        logger.error(f"failed to load data from '{data_source}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def _normalize_v1_result(result: dict) -> dict:
    '''
    normalize v1 result format to standard format
    '''
    if isinstance(result, dict):
        # ensure anomalies key exists
        if "anomalies" not in result:
            # if result has anomaly-like structure, wrap it
            if "anomaly" in result or "risk_score" in result:
                result = {"anomalies": [result], **result}
            else:
                result["anomalies"] = result.get("anomalies", [])
        return result
    else:
        return {"result": result, "anomalies": []}


def _save_trained_artifact(model_instance) -> dict:
    '''
    serialize a trained model to persistent storage after training.
    returns artifact info dict with path, format, file_hash, or empty dict on failure.
    '''
    slug = os.getenv("MODEL_SLUG", "unknown")
    version = os.getenv("MODEL_VERSION", "0.0.0")
    run_id = os.getenv("RUN_ID")
    runtime = os.getenv("MODEL_RUNTIME", "python-base")
    saved_models_base = os.getenv("SAVED_MODELS_PATH", "/opt/openuba/saved_models")

    if not run_id:
        logger.warning("no RUN_ID set, skipping artifact save")
        return {}

    artifact_dir = Path(saved_models_base) / slug / version / run_id
    try:
        artifact_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"failed to create artifact directory {artifact_dir}: {e}")
        return {}

    artifact_file = None
    artifact_format = "pickle"

    try:
        if runtime == "sklearn":
            import joblib
            artifact_file = artifact_dir / "model.pkl"
            joblib.dump(model_instance.model, artifact_file)
            artifact_format = "sklearn_pickle"
            logger.info(f"saved sklearn artifact to {artifact_file}")
        elif runtime == "pytorch":
            import torch
            artifact_file = artifact_dir / "model.pt"
            torch.save(model_instance.model.state_dict(), artifact_file)
            artifact_format = "torch_pt"
            logger.info(f"saved pytorch artifact to {artifact_file}")
        elif runtime == "tensorflow":
            artifact_file = artifact_dir / "model_tf"
            model_instance.model.save(str(artifact_file))
            artifact_format = "tf_saved_model"
            logger.info(f"saved tensorflow artifact to {artifact_file}")
        else:
            import pickle
            artifact_file = artifact_dir / "model.pkl"
            with open(artifact_file, "wb") as f:
                pickle.dump(model_instance, f)
            artifact_format = "pickle"
            logger.info(f"saved generic pickle artifact to {artifact_file}")
    except Exception as e:
        logger.error(f"failed to serialize model artifact: {e}")
        return {}

    # compute file hash
    file_hash = ""
    if artifact_file and artifact_file.exists():
        file_hash = hash_file(artifact_file)

    return {
        "path": str(artifact_file),
        "format": artifact_format,
        "file_hash": file_hash,
        "artifact_dir": str(artifact_dir)
    }


def _load_trained_artifact(model_instance) -> bool:
    '''
    load a previously trained artifact into the model instance before inference.
    returns True if artifact was loaded, False otherwise.
    '''
    artifact_path = os.getenv("ARTIFACT_PATH")
    runtime = os.getenv("MODEL_RUNTIME", "python-base")

    if not artifact_path:
        logger.info("no ARTIFACT_PATH set, model will use default/untrained state")
        return False

    if not os.path.exists(artifact_path):
        logger.warning(f"artifact path does not exist: {artifact_path}")
        return False

    try:
        if runtime == "sklearn":
            import joblib
            model_instance.model = joblib.load(artifact_path)
            if hasattr(model_instance, "is_trained"):
                model_instance.is_trained = True
            logger.info(f"loaded sklearn artifact from {artifact_path}")
        elif runtime == "pytorch":
            import torch
            model_instance.model.load_state_dict(torch.load(artifact_path))
            if hasattr(model_instance, "is_trained"):
                model_instance.is_trained = True
            logger.info(f"loaded pytorch artifact from {artifact_path}")
        elif runtime == "tensorflow":
            import tensorflow as tf
            model_instance.model = tf.keras.models.load_model(artifact_path)
            if hasattr(model_instance, "is_trained"):
                model_instance.is_trained = True
            logger.info(f"loaded tensorflow artifact from {artifact_path}")
        else:
            import pickle
            with open(artifact_path, "rb") as f:
                loaded = pickle.load(f)
            # copy attributes from loaded model to instance
            for attr in vars(loaded):
                setattr(model_instance, attr, getattr(loaded, attr))
            logger.info(f"loaded generic pickle artifact from {artifact_path}")
        return True
    except Exception as e:
        logger.error(f"failed to load artifact from {artifact_path}: {e}")
        return False


def main():
    '''
    main entry point
    '''
    # get environment variables
    model_id = os.getenv("MODEL_ID")
    execution_id = os.getenv("EXECUTION_ID")
    run_id = os.getenv("RUN_ID")
    model_path = Path(os.getenv("MODEL_PATH", "/model"))
    input_data_file = os.getenv("INPUT_DATA_FILE")
    run_type = os.getenv("RUN_TYPE", "infer")
    input_data_json = os.getenv("INPUT_DATA")

    logger.info(f"starting model runner: model_id={model_id}, execution_id={execution_id}, run_id={run_id}, run_type={run_type}")

    # verify model path exists
    if not model_path.exists():
        logger.error(f"model path does not exist: {model_path}")
        sys.exit(1)

    # load input data if provided (check multiple sources)
    input_data = None
    if input_data_json:
        try:
            input_data = json.loads(input_data_json)
        except json.JSONDecodeError:
            logger.warning("invalid input_data json, trying file")
    if not input_data and input_data_file and os.path.exists(input_data_file):
        with open(input_data_file, "r") as f:
            input_data = json.load(f)
    # K8s mode: operator passes config/input path as UBA_CONFIG_PATH or UBA_INPUT_PATH
    if not input_data:
        k8s_input_path = os.getenv("UBA_CONFIG_PATH") or os.getenv("UBA_INPUT_PATH")
        if k8s_input_path and os.path.exists(k8s_input_path):
            try:
                with open(k8s_input_path, "r") as f:
                    input_data = json.load(f)
                logger.info(f"loaded input data from {k8s_input_path}")
            except Exception as e:
                logger.warning(f"failed to load input from {k8s_input_path}: {e}")

    # verify model files (if expected hashes provided via env)
    expected_hashes_json = os.getenv("EXPECTED_HASHES")
    if expected_hashes_json:
        try:
            expected_hashes = json.loads(expected_hashes_json)
            if not verify_model_files(model_path, expected_hashes):
                logger.error("model file verification failed")
                sys.exit(1)
        except json.JSONDecodeError:
            logger.warning("invalid expected_hashes json, skipping verification")

    # update model run status if run_id and DATABASE_URL provided
    db_url = os.getenv("DATABASE_URL")
    if run_id and db_url:
        try:
            from sqlalchemy import create_engine, text
            from datetime import datetime
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE model_runs SET status = :status, started_at = :started_at WHERE id = :run_id"),
                    {"status": "running", "started_at": datetime.utcnow(), "run_id": run_id}
                )
                conn.commit()
            engine.dispose()
        except Exception as e:
            logger.warning(f"failed to update model run status: {e}")

    # attach DB log handler if DATABASE_URL and run_id are available
    db_log_handler = None
    db_url = os.getenv("DATABASE_URL")
    if db_url and run_id:
        try:
            db_log_handler = ModelLogHandler(run_id=run_id, db_url=db_url)
            db_log_handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(db_log_handler)
            logger.info(f"model log capture enabled for run {run_id}")
        except Exception as e:
            logger.warning(f"failed to attach DB log handler: {e}")
            db_log_handler = None

    # execute model
    try:
        result = execute_model(model_path, input_data, run_type=run_type)
        
        # if training succeeded, register artifact in DB
        if run_id and db_url and run_type == "train" and result.get("status") == "success":
            artifact_info = result.get("artifact_info", {})
            if artifact_info and artifact_info.get("file_hash"):
                try:
                    from sqlalchemy import create_engine, text
                    from datetime import datetime
                    import uuid

                    engine = create_engine(db_url)
                    with engine.connect() as conn:
                        # get model_version_id from the run
                        row = conn.execute(
                            text("SELECT model_version_id FROM model_runs WHERE id = :run_id"),
                            {"run_id": run_id}
                        ).fetchone()
                        if row:
                            model_version_id = row[0]
                            artifact_id = str(uuid.uuid4())
                            metrics_json = json.dumps(result.get("training_result", {}))

                            conn.execute(
                                text(
                                    "INSERT INTO model_artifacts (id, model_version_id, kind, format, path, metrics, file_hash) "
                                    "VALUES (:id, :mvid, :kind, :format, :path, CAST(:metrics AS jsonb), :file_hash)"
                                ),
                                {
                                    "id": artifact_id,
                                    "mvid": model_version_id,
                                    "kind": "checkpoint",
                                    "format": artifact_info["format"],
                                    "path": artifact_info["path"],
                                    "metrics": metrics_json,
                                    "file_hash": artifact_info["file_hash"]
                                }
                            )

                            # link artifact to run and mark succeeded
                            result_json = json.dumps(result)
                            conn.execute(
                                text(
                                    "UPDATE model_runs SET artifact_id = :aid, status = 'succeeded', "
                                    "finished_at = :finished, result_summary = CAST(:summary AS jsonb) WHERE id = :run_id"
                                ),
                                {
                                    "aid": artifact_id,
                                    "finished": datetime.utcnow(),
                                    "summary": result_json,
                                    "run_id": run_id
                                }
                            )
                            conn.commit()
                            logger.info(f"registered artifact {artifact_id} in DB: {artifact_info['path']}")
                    engine.dispose()
                except Exception as e:
                    logger.warning(f"failed to create artifact in DB: {e}")
            else:
                logger.warning("training succeeded but no artifact was saved (missing file_hash)")
        
        # update model run status on success and persist anomalies
        if run_id and db_url and run_type == "infer":
            try:
                from sqlalchemy import create_engine, text
                from datetime import datetime
                import uuid as _uuid

                result_json = json.dumps(result)
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            "UPDATE model_runs SET status = 'succeeded', finished_at = :finished, "
                            "result_summary = CAST(:summary AS jsonb) WHERE id = :run_id"
                        ),
                        {"finished": datetime.utcnow(), "summary": result_json, "run_id": run_id}
                    )

                    # persist anomalies to the anomalies table
                    anomalies_list = result.get("anomalies", [])
                    if anomalies_list:
                        logger.info(f"persisting {len(anomalies_list)} anomalies to database...")
                        # resolve model UUID: model_runs → model_versions → models
                        row = conn.execute(
                            text(
                                "SELECT mv.model_id FROM model_runs mr "
                                "JOIN model_versions mv ON mr.model_version_id = mv.id "
                                "WHERE mr.id = :run_id"
                            ),
                            {"run_id": run_id}
                        ).fetchone()
                        model_uuid = str(row[0]) if row else None

                        if model_uuid:
                            anomaly_rows = []
                            for a in anomalies_list:
                                anomaly_rows.append({
                                    "id": str(_uuid.uuid4()),
                                    "model_id": model_uuid,
                                    "run_id": run_id,
                                    "entity_id": str(a.get("entity_id", "unknown")),
                                    "entity_type": a.get("entity_type", "user"),
                                    "risk_score": float(a.get("risk_score", 0)),
                                    "anomaly_type": a.get("anomaly_type", "unknown"),
                                    "details": json.dumps(a.get("details", {})),
                                })

                            # batch insert for large datasets
                            batch_size = 5000
                            total = len(anomaly_rows)
                            for batch_start in range(0, total, batch_size):
                                batch = anomaly_rows[batch_start:batch_start + batch_size]
                                conn.execute(
                                    text(
                                        "INSERT INTO anomalies (id, model_id, run_id, entity_id, entity_type, risk_score, anomaly_type, details) "
                                        "VALUES (:id, :model_id, :run_id, :entity_id, :entity_type, :risk_score, :anomaly_type, CAST(:details AS jsonb))"
                                    ),
                                    batch
                                )
                                if total > batch_size:
                                    logger.info(f"persisted batch {batch_start + len(batch)}/{total} anomalies")
                            logger.info(f"persisted {total} anomalies to database")

                    conn.commit()
                engine.dispose()
            except Exception as e:
                logger.warning(f"failed to update model run status: {e}")
        
        # flush DB logs before exiting
        if db_log_handler:
            db_log_handler.flush()
            logger.removeHandler(db_log_handler)

        # output result as json to stdout
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        logger.error(f"execution failed: {e}")
        
        # update model run status on failure
        if run_id and db_url:
            try:
                from sqlalchemy import create_engine, text
                from datetime import datetime

                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            "UPDATE model_runs SET status = 'failed', finished_at = :finished, "
                            "error_message = :error WHERE id = :run_id"
                        ),
                        {"finished": datetime.utcnow(), "error": str(e), "run_id": run_id}
                    )
                    conn.commit()
                engine.dispose()
            except Exception as db_err:
                logger.warning(f"failed to update model run status: {db_err}")
        
        # flush DB logs before exiting on failure
        if db_log_handler:
            db_log_handler.flush()
            logger.removeHandler(db_log_handler)

        error_result = {
            "error": str(e),
            "model_id": model_id,
            "execution_id": execution_id,
            "run_id": run_id
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()

