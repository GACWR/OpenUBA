'''
Copyright 2019-Present The OpenUBA Platform Authors
data ingestion service for loading data into spark and elasticsearch
'''

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.integrations.spark import SparkConnector
from core.integrations.elasticsearch import ElasticsearchConnector

logger = logging.getLogger(__name__)


class DataIngestionService:
    '''
    service for ingesting data from test_datasets into spark and elasticsearch
    '''

    def __init__(
        self,
        spark_master_url: Optional[str] = None,
        elasticsearch_hosts: Optional[List[str]] = None
    ):
        self.spark_connector = SparkConnector(
            master_url=spark_master_url or os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
        )
        self.es_connector = ElasticsearchConnector(
            hosts=elasticsearch_hosts or [os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")]
        )
        # support both absolute and relative paths
        test_datasets_env = os.getenv("TEST_DATASETS_PATH", "test_datasets")
        if os.path.isabs(test_datasets_env):
            self.test_datasets_path = Path(test_datasets_env)
        else:
            # try relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.test_datasets_path = project_root / test_datasets_env

    def ingest_to_spark(
        self,
        dataset_path: str,
        table_name: str,
        format: str = "csv",
        **options
    ) -> Dict[str, Any]:
        '''
        ingest data from file path into spark table
        '''
        try:
            self.spark_connector.connect()
            df = self.spark_connector.read_data(dataset_path, format=format, **options)
            
            if df is None:
                logger.warning(f"failed to read data from {dataset_path}, skipping spark ingestion")
                return {
                    "status": "skipped",
                    "reason": "failed to read data",
                    "table_name": table_name
                }

            # write to spark table
            # register external table (no data copy)
            self.spark_connector.spark.sql(f"DROP TABLE IF EXISTS {table_name}")

            # construct options string
            opt_str = ", ".join([f"'{k}' '{v}'" for k, v in options.items()])
            
            # create table pointing to existing file
            query = f"""
                CREATE TABLE {table_name}
                USING {format}
                OPTIONS ({opt_str})
                LOCATION '{dataset_path}'
            """
            logger.info(f"executing spark ddl: {query}")
            self.spark_connector.spark.sql(query)
            
            # verify count
            df = self.spark_connector.spark.table(table_name)
            
            row_count = df.count()
            logger.info(f"ingested {row_count} rows into spark table: {table_name}")
            
            return {
                "status": "success",
                "table_name": table_name,
                "row_count": row_count,
                "format": format
            }
        except Exception as e:
            logger.error(f"failed to ingest to spark: {e}")
            raise

    def ingest_to_elasticsearch(
        self,
        dataset_path: str,
        index_name: str,
        format: str = "csv",
        **options
    ) -> Dict[str, Any]:
        '''
        ingest data from file path into elasticsearch index
        '''
        try:
            self.es_connector.connect()
            
            # read file and parse
            import pandas as pd
            
            if format == "csv":
                # handle encoding for legacy logs (like bluecoat proxy)
                encoding = options.get("encoding", "utf-8")
                try:
                    # try specified encoding or utf-8 first
                    df = pd.read_csv(
                        dataset_path,
                        sep=options.get("sep", ","),
                        header=options.get("header", 0),
                        encoding=encoding
                    )
                except UnicodeDecodeError:
                    logger.warning(f"utf-8 decoding failed for {dataset_path}, trying latin-1")
                    # fallback to latin-1
                    df = pd.read_csv(
                        dataset_path,
                        sep=options.get("sep", ","),
                        header=options.get("header", 0),
                        encoding="latin-1"
                    )
            elif format == "json":
                df = pd.read_json(dataset_path)
            else:
                raise ValueError(f"unsupported format for es ingestion: {format}")
            
            # convert to list of dicts
            df = df.where(pd.notnull(df), None)
            documents = df.to_dict("records")
            
            # add timestamp if not present
            for doc in documents:
                if "timestamp" not in doc and "@timestamp" not in doc:
                    doc["@timestamp"] = datetime.utcnow().isoformat()
            
            # create index if needed (overwrite)
            self.es_connector.delete_index(index_name)
            self.es_connector.create_index(index_name)
            
            # bulk index
            result = self.es_connector.bulk_index(documents, index_name)
            
            logger.info(f"ingested {result['success']} documents into elasticsearch index: {index_name}")
            
            return {
                "status": "success",
                "index_name": index_name,
                "document_count": result["success"],
                "failed": result["failed"]
            }
        except Exception as e:
            logger.error(f"failed to ingest to elasticsearch: {e}")
            raise

    def create_run(self, dataset_name: str) -> str:
        '''
        create a new ingestion run record
        '''
        from core.db.connection import get_db_context
        from sqlalchemy import text
        
        with get_db_context() as db:
            result = db.execute(
                text("""
                    INSERT INTO data_ingestion_runs (dataset_name, status, started_at)
                    VALUES (:dataset_name, 'running', NOW())
                    RETURNING id
                """),
                {"dataset_name": dataset_name}
            )
            run_id = str(result.scalar())
            db.commit()
            return run_id

    def update_run_status(self, run_id: str, status: str, details: Dict[str, Any] = None, error: str = None):
        '''
        update run status and details
        '''
        from core.db.connection import get_db_context
        from sqlalchemy import text
        import json
        
        with get_db_context() as db:
            params = {
                "id": run_id,
                "status": status,
                "error": error
            }
            
            query = """
                UPDATE data_ingestion_runs 
                SET status = :status, updated_at = NOW()
            """
            
            if status in ['completed', 'failed']:
                query += ", completed_at = NOW()"
                
            if details:
                params["details"] = json.dumps(details)
                query += ", details = :details"
                
            if error:
                query += ", error_message = :error"
                
            query += " WHERE id = :id"
            
            db.execute(text(query), params)
            db.commit()

    def ingest_from_test_datasets(
        self,
        dataset_name: str = "toy_1",
        ingest_to_spark: bool = True,
        ingest_to_es: bool = True,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        '''
        ingest all data from test_datasets/{dataset_name} into spark and/or elasticsearch
        expects structure: test_datasets/{dataset_name}/{log_type}/{log_file}
        '''
        # if no run_id provided, create one (for backward compatibility/manual calls)
        if not run_id:
            try:
                run_id = self.create_run(dataset_name)
            except Exception as e:
                logger.warning(f"failed to create run record: {e}")

        results = {
            "dataset": dataset_name,
            "spark": {},
            "elasticsearch": {},
            "errors": []
        }
        
        try:
            dataset_path = self.test_datasets_path / dataset_name
            if not dataset_path.exists():
                raise ValueError(f"dataset not found: {dataset_path}")
            
            logger.info(f"starting ingestion for dataset: {dataset_name} from {dataset_path}")
            
            # iterate through log types (dhcp, dns, proxy, ssh)
            for log_type_dir in dataset_path.iterdir():
                if not log_type_dir.is_dir():
                    continue
                
                log_type = log_type_dir.name
                logger.info(f"processing log type: {log_type}")
                
                # find log files in directory
                for log_file in log_type_dir.iterdir():
                    if not log_file.is_file():
                        continue
                    
                    file_path = str(log_file)
                    table_name = f"{dataset_name}_{log_type}"
                    index_name = f"openuba-{log_type}-{dataset_name}"
                    
                    logger.info(f"found log file: {log_file.name} ({log_file.stat().st_size} bytes)")
                    
                    try:
                        # determine format from file extension and log type
                        if log_file.suffix == ".csv" or log_file.suffix == ".log":
                            format_type = "csv"
                            if log_type in ["ssh", "dns", "dhcp"]:
                                spark_options = {"sep": "\t", "header": "false"}
                                pandas_options = {"sep": "\t", "header": None}
                            elif log_type in ["proxy", "bluecoat"]:
                                # spark uses ISO-8859-1 for latin-1
                                spark_options = {"sep": " ", "header": "true", "encoding": "ISO-8859-1"}
                                pandas_options = {"sep": " ", "header": 0, "encoding": "latin-1"}
                            else:
                                # default for proxy/bluecoat and others
                                spark_options = {"sep": " ", "header": "true"}
                                pandas_options = {"sep": " ", "header": 0}
                        elif log_file.suffix == ".parquet":
                            format_type = "parquet"
                            spark_options = {}
                            pandas_options = {}
                        elif log_file.suffix == ".json":
                            format_type = "json"
                            spark_options = {}
                            pandas_options = {}
                        else:
                            logger.warning(f"unknown file format: {log_file.suffix}, skipping")
                            continue
                        
                        logger.debug(f"format detected: {format_type}, spark_options: {spark_options}, pandas_options: {pandas_options}")
                        
                        # ingest to spark
                        if ingest_to_spark:
                            try:
                                logger.info(f"ingesting to spark table: {table_name}")
                                spark_result = self.ingest_to_spark(
                                    file_path,
                                    table_name,
                                    format=format_type,
                                    **spark_options
                                )
                                results["spark"][log_type] = spark_result
                                if "row_count" in spark_result:
                                    logger.info(f"spark ingestion success: {spark_result['row_count']} rows")
                                else:
                                    logger.warning(f"spark ingestion skipped or failed: {spark_result.get('reason', 'unknown')}")
                            except Exception as e:
                                error_msg = f"spark ingestion failed for {log_type}: {e}"
                                logger.error(error_msg)
                                results["errors"].append(error_msg)
                        
                        # ingest to elasticsearch
                        if ingest_to_es:
                            try:
                                logger.info(f"ingesting to elasticsearch index: {index_name}")
                                es_result = self.ingest_to_elasticsearch(
                                    file_path,
                                    index_name,
                                    format=format_type,
                                    **pandas_options
                                )
                                results["elasticsearch"][log_type] = es_result
                                logger.info(f"elasticsearch ingestion success: {es_result['document_count']} docs")
                            except Exception as e:
                                error_msg = f"elasticsearch ingestion failed for {log_type}: {e}"
                                logger.error(error_msg)
                                results["errors"].append(error_msg)
                    
                    except Exception as e:
                        error_msg = f"failed to process {log_type}/{log_file.name}: {e}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
            
            # update run status
            if run_id:
                # Check for partial success
                has_success = any(results.get(k) for k in ["elasticsearch", "spark"])
                
                if not results["errors"]:
                    status = "completed"
                elif has_success:
                    status = "completed" # Mark as completed even with errors if we ingested something
                    logger.warning(f"ingestion run {run_id} completed with errors: {results['errors']}")
                else:
                    status = "failed"

                self.update_run_status(run_id, status, results, str(results["errors"]) if results["errors"] else None)
                logger.info(f"ingestion run {run_id} finished with status: {status}")
                
        except Exception as e:
            logger.error(f"ingestion failed: {e}")
            if run_id:
                self.update_run_status(run_id, "failed", results, str(e))
            raise

        return results

    def ingest_all_datasets(
        self,
        ingest_to_spark: bool = True,
        ingest_to_es: bool = True
    ) -> Dict[str, Any]:
        '''
        ingest ALL datasets found in test_datasets directory
        '''
        results = {
            "datasets": {},
            "total_datasets": 0,
            "errors": []
        }
        
        try:
            if not self.test_datasets_path.exists():
                raise ValueError(f"test_datasets path not found: {self.test_datasets_path}")

            # Check for nested mount (if test_datasets folder exists inside test_datasets)
            # This happens if project root is mounted to /app/test_datasets
            adjusted_path = self.test_datasets_path
            
            # Log contents for debugging
            try:
                contents = [x.name for x in self.test_datasets_path.iterdir()]
                logger.info(f"contents of {self.test_datasets_path}: {contents}")
            except Exception as e:
                logger.error(f"failed to list {self.test_datasets_path}: {e}")

            # SEARCH FOR toy_1
            # If toy_1 is not in root, look for it in subdirectories
            toy_1_path = adjusted_path / "toy_1"
            if not toy_1_path.exists():
                # Try to find it in immediate subdirectories (e.g. test_datasets/toy_1)
                found = False
                for item in adjusted_path.iterdir():
                    if item.is_dir():
                        candidate = item / "toy_1"
                        if candidate.exists() and candidate.is_dir():
                            logger.info(f"found toy_1 in nested path: {candidate}")
                            adjusted_path = item # Use the parent of toy_1 as the base
                            found = True
                            break
                if not found:
                    logger.warning(f"toy_1 not found in {adjusted_path} or its subdirectories")

            logger.info(f"scanning for datasets in {adjusted_path}")
            
            # Iterate over all subdirectories
            for item in adjusted_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    dataset_name = item.name
                    
                    # STRICT WHITELIST: only allow toy_1 (user request)
                    if dataset_name != "toy_1":
                        logger.warning(f"skipping invalid dataset: {dataset_name} (only 'toy_1' is allowed per user rule)")
                        continue

                    logger.info(f"found dataset: {dataset_name}")
                    
                    try:
                        # process this dataset
                        dataset_result = self.ingest_from_test_datasets(
                            dataset_name=dataset_name,
                            ingest_to_spark=ingest_to_spark,
                            ingest_to_es=ingest_to_es
                        )
                        results["datasets"][dataset_name] = dataset_result
                        results["total_datasets"] += 1
                    except Exception as e:
                        error_msg = f"failed to ingest dataset {dataset_name}: {e}"
                        logger.error(error_msg)
                        results["datasets"][dataset_name] = {"status": "failed", "error": str(e)} # Add this to results so UI sees it
                        results["errors"].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"ingest all failed: {e}")
            raise

    def get_spark_metrics(self) -> Dict[str, Any]:
        '''
        get metrics about spark tables
        '''
        try:
            self.spark_connector.connect()
            tables = self.spark_connector.list_tables()
            metrics = {}
            for table in tables:
                try:
                    info = self.spark_connector.get_table_info(table)
                    metrics[table] = info
                except Exception as e:
                    logger.warning(f"failed to get info for table {table}: {e}")
            return {
                "status": "success",
                "tables": metrics,
                "total_tables": len(metrics)
            }
        except Exception as e:
            logger.error(f"failed to get spark metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tables": {},
                "total_tables": 0
            }

    def get_elasticsearch_metrics(self) -> Dict[str, Any]:
        '''
        get metrics about elasticsearch indices
        '''
        try:
            self.es_connector.connect()
            indices = self.es_connector.list_indices()
            metrics = {}
            for index in indices:
                try:
                    stats = self.es_connector.get_index_stats(index)
                    metrics[index] = stats
                except Exception as e:
                    logger.warning(f"failed to get stats for index {index}: {e}")
            return {
                "status": "success",
                "indices": metrics,
                "total_indices": len(metrics)
            }
        except Exception as e:
            logger.error(f"failed to get elasticsearch metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "indices": {},
                "total_indices": 0
            }

