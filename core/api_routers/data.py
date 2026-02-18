'''
Copyright 2019-Present The OpenUBA Platform Authors
data ingestion and metrics api endpoints
'''

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel

from core.db import get_db
from core.services.data_ingestion import DataIngestionService
from core.auth import require_permission
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["data"])


class IngestRequest(BaseModel):
    dataset_name: str = "toy_1"
    ingest_to_spark: bool = True
    ingest_to_es: bool = True
    ingest_all: bool = False


@router.post("/ingest")
async def ingest_data(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    ingest data from test_datasets into spark and/or elasticsearch
    '''
    try:
        service = DataIngestionService()
        
        if request.ingest_all:
            # create run record for "all" is tricky, maybe just one global run?
            # actually ingest_all_datasets creates multiple calls internally probably? 
            # No, my implementation calls ingest_from_test_datasets which allows separate run_ids.
            # For simplicity, we just launch the task.
            
            background_tasks.add_task(
                service.ingest_all_datasets,
                ingest_to_spark=request.ingest_to_spark,
                ingest_to_es=request.ingest_to_es
            )
            return {
                "status": "accepted",
                "message": "batch ingestion started in background (all datasets)"
            }
            
        # create run record first
        run_id = service.create_run(request.dataset_name)
        
        # run ingestion in background
        background_tasks.add_task(
            service.ingest_from_test_datasets,
            dataset_name=request.dataset_name,
            ingest_to_spark=request.ingest_to_spark,
            ingest_to_es=request.ingest_to_es,
            run_id=run_id
        )
        
        return {
            "status": "accepted",
            "run_id": run_id,
            "message": "ingestion started in background"
        }
    except Exception as e:
        logger.error(f"data ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-from-path")
async def ingest_from_path(
    file_path: str,
    table_name: Optional[str] = None,
    index_name: Optional[str] = None,
    format: str = "csv",
    ingest_to_spark: bool = True,
    ingest_to_es: bool = True,
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    ingest data from a specific file path
    '''
    try:
        service = DataIngestionService()
        results = {}
        
        if ingest_to_spark and table_name:
            spark_result = service.ingest_to_spark(file_path, table_name, format=format)
            results["spark"] = spark_result
        
        if ingest_to_es and index_name:
            es_result = service.ingest_to_elasticsearch(file_path, index_name, format=format)
            results["elasticsearch"] = es_result
        
        return results
    except Exception as e:
        logger.error(f"data ingestion from path failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/spark")
async def get_spark_metrics(
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    get metrics about spark tables (row counts, schemas, freshness)
    '''
    import asyncio

    def _fetch_spark_metrics():
        service = DataIngestionService()
        metrics = service.get_spark_metrics()

        from core.integrations.spark import SparkConnector
        spark_connector = SparkConnector()
        try:
            spark_connector.connect()
            enhanced_metrics = metrics.copy()
            for table_name in metrics.get("tables", {}).keys():
                try:
                    table_info = spark_connector.get_table_info(table_name)
                    if table_info:
                        enhanced_metrics["tables"][table_name].update({
                            "schema": table_info.get("schema"),
                            "partition_count": table_info.get("partition_count", 0)
                        })
                except Exception as e:
                    logger.warning(f"failed to get schema for table {table_name}: {e}")
        finally:
            spark_connector.close()

        return enhanced_metrics

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_spark_metrics),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("spark metrics timed out after 30s")
        # return basic metrics without schema info
        try:
            service = DataIngestionService()
            return service.get_spark_metrics()
        except Exception:
            return {"status": "timeout", "tables": {}}
    except Exception as e:
        logger.error(f"failed to get spark metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/elasticsearch")
async def get_elasticsearch_metrics(
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    get metrics about elasticsearch indices (document counts, sizes, mappings)
    '''
    try:
        service = DataIngestionService()
        metrics = service.get_elasticsearch_metrics()
        
        # enhance with mapping information
        from core.integrations.elasticsearch import ElasticsearchConnector
        es_connector = ElasticsearchConnector()
        try:
            es_connector.connect()
            enhanced_metrics = metrics.copy()
            for index_name in metrics.get("indices", {}).keys():
                try:
                    # get index mapping
                    mapping = es_connector.client.indices.get_mapping(index=index_name)
                    if mapping and index_name in mapping:
                        enhanced_metrics["indices"][index_name]["mapping"] = mapping[index_name].get("mappings", {})
                    
                    # get index settings for freshness info
                    settings = es_connector.client.indices.get_settings(index=index_name)
                    if settings and index_name in settings:
                        enhanced_metrics["indices"][index_name]["settings"] = settings[index_name].get("settings", {})
                except Exception as e:
                    logger.warning(f"failed to get mapping for index {index_name}: {e}")
        finally:
            es_connector.close()
        
        return enhanced_metrics
    except Exception as e:
        logger.error(f"failed to get elasticsearch metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_all_metrics(
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    get metrics from both spark and elasticsearch
    '''
    try:
        service = DataIngestionService()
        return {
            "spark": service.get_spark_metrics(),
            "elasticsearch": service.get_elasticsearch_metrics()
        }
    except Exception as e:
        logger.error(f"failed to get all metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_ingestion_history(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("data"))
) -> Dict[str, Any]:
    '''
    get ingestion volume history for the last N days
    '''
    from sqlalchemy import text
    from datetime import datetime, timedelta
    import json
    
    try:
        # query completed runs in the last N days
        query = text("""
            SELECT 
                DATE(completed_at) as date,
                details
            FROM data_ingestion_runs
            WHERE status = 'completed'
            AND completed_at >= NOW() - INTERVAL ':days days'
            ORDER BY date ASC
        """)
        
        result = db.execute(query, {"days": days})
        rows = result.fetchall()
        
        # aggregate by date — track spark and elasticsearch separately
        daily_spark = {}
        daily_es = {}

        # initialize last N days with 0
        today = datetime.now().date()
        for i in range(days):
            d = (today - timedelta(days=i)).isoformat()
            daily_spark[d] = 0
            daily_es[d] = 0

        for row in rows:
            date_str = str(row[0])
            details = row[1]

            if isinstance(details, str):
                details = json.loads(details)

            # sum elasticsearch docs
            es_count = 0
            if "elasticsearch" in details:
                for idx, stats in details["elasticsearch"].items():
                    es_count += stats.get("document_count", 0)

            # sum spark rows
            spark_count = 0
            if "spark" in details:
                for table, stats in details["spark"].items():
                    spark_count += stats.get("row_count", 0)

            # approximate size in MB (assuming 1KB per doc/row avg)
            es_mb = (es_count * 1024) / (1024 * 1024)
            spark_mb = (spark_count * 1024) / (1024 * 1024)

            if date_str in daily_es:
                daily_es[date_str] += es_mb
            else:
                daily_es[date_str] = es_mb

            if date_str in daily_spark:
                daily_spark[date_str] += spark_mb
            else:
                daily_spark[date_str] = spark_mb

        # format for chart — include both spark and elasticsearch values
        chart_data = [
            {
                "name": d,
                "value": round(daily_spark.get(d, 0) + daily_es.get(d, 0), 2),
                "spark": round(daily_spark.get(d, 0), 2),
                "elasticsearch": round(daily_es.get(d, 0), 2)
            }
            for d in sorted(set(list(daily_spark.keys()) + list(daily_es.keys())))
        ]

        return {
            "history": chart_data
        }
    except Exception as e:
        logger.error(f"failed to get ingestion history: {e}")
        # return empty history on error to avoid breaking UI
        return {"history": []}
