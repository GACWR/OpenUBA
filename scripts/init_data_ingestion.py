#!/usr/bin/env python3
'''
Copyright 2019-Present The OpenUBA Platform Authors
initialization script for data ingestion on first setup
'''

import os
import sys
import logging
import time
from pathlib import Path

# add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.data_ingestion import DataIngestionService
from core.integrations.spark import SparkConnector
from core.integrations.elasticsearch import ElasticsearchConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def wait_for_service(service_name: str, check_func, max_wait: int = 300, interval: int = 5):
    '''
    wait for a service to be ready
    '''
    logger.info(f"waiting for {service_name} to be ready...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            if check_func():
                logger.info(f"{service_name} is ready")
                return True
        except Exception as e:
            logger.debug(f"{service_name} not ready yet: {e}")
        time.sleep(interval)
    logger.error(f"{service_name} not ready after {max_wait} seconds")
    return False


def check_spark_ready():
    '''
    check if spark is ready
    '''
    try:
        connector = SparkConnector()
        connector.connect()
        connector.close()
        return True
    except Exception:
        return False


def check_elasticsearch_ready():
    '''
    check if elasticsearch is ready
    '''
    try:
        connector = ElasticsearchConnector()
        connector.connect()
        return True
    except Exception:
        return False


def check_data_already_ingested():
    '''
    check if data has already been ingested
    returns (spark_ingested, es_ingested)
    '''
    spark_ingested = False
    es_ingested = False
    
    try:
        service = DataIngestionService()
        spark_metrics = service.get_spark_metrics()
        if spark_metrics.get("total_tables", 0) > 0:
            spark_ingested = True
            logger.info(f"spark already has {spark_metrics['total_tables']} tables")
    except Exception as e:
        logger.debug(f"could not check spark metrics: {e}")
    
    try:
        service = DataIngestionService()
        es_metrics = service.get_elasticsearch_metrics()
        if es_metrics.get("total_indices", 0) > 0:
            es_ingested = True
            logger.info(f"elasticsearch already has {es_metrics['total_indices']} indices")
    except Exception as e:
        logger.debug(f"could not check es metrics: {e}")
    
    return spark_ingested, es_ingested


def main():
    '''
    main initialization function
    '''
    logger.info("starting data ingestion initialization")
    
    # wait for services to be ready
    spark_ready = wait_for_service("spark", check_spark_ready, max_wait=600)
    es_ready = wait_for_service("elasticsearch", check_elasticsearch_ready, max_wait=600)
    
    if not spark_ready and not es_ready:
        logger.error("neither spark nor elasticsearch is ready, aborting")
        sys.exit(1)
    
    # check if data already ingested
    spark_ingested, es_ingested = check_data_already_ingested()
    
    if spark_ingested and es_ingested:
        logger.info("data already ingested, skipping")
        return
    
    # get dataset path
    dataset_name = os.getenv("DATASET_NAME", "toy_1")
    test_datasets_path = Path(os.getenv("TEST_DATASETS_PATH", "/app/test_datasets"))
    dataset_path = test_datasets_path / dataset_name
    
    # also check project root for local development
    if not dataset_path.exists():
        local_path = project_root / "test_datasets" / dataset_name
        if local_path.exists():
            test_datasets_path = project_root / "test_datasets"
            dataset_path = local_path
            logger.info(f"using local dataset path: {dataset_path}")
        else:
            logger.warning(f"dataset path does not exist: {dataset_path} or {local_path}")
            logger.info("skipping data ingestion - dataset not found")
            return
    
    # update service with correct path
    os.environ["TEST_DATASETS_PATH"] = str(test_datasets_path)
    
    # ingest data
    try:
        service = DataIngestionService()
        logger.info(f"ingesting data from {dataset_path}")
        
        results = service.ingest_from_test_datasets(
            dataset_name=dataset_name,
            ingest_to_spark=spark_ready and not spark_ingested,
            ingest_to_es=es_ready and not es_ingested
        )
        
        logger.info("data ingestion completed")
        logger.info(f"spark results: {len(results.get('spark', {}))} tables")
        logger.info(f"elasticsearch results: {len(results.get('elasticsearch', {}))} indices")
        
        if results.get("errors"):
            logger.warning(f"some errors occurred: {results['errors']}")
        
    except Exception as e:
        logger.error(f"data ingestion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

