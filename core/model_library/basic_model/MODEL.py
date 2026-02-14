'''
Copyright 2019-Present The OpenUBA Platform Authors
basic model template using data adapters
this model demonstrates how to use spark and elasticsearch data adapters
supports both v1 (execute) and v2 (train/infer) interfaces
'''

import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


# v1 interface (backward compatibility)
def execute(input_data: Dict[str, Any] = None) -> Dict[str, Any]:
    '''
    v1 interface: execute function for backward compatibility
    '''
    logger.info("executing basic model (v1 interface)")
    return _execute_inference(input_data)


# v2 interface (preferred)
class Model:
    '''
    v2 model interface following model-lifecycle spec
    '''
    
    def train(self, ctx) -> Dict[str, Any]:
        '''
        train the model (optional - this is an inference-only model)
        '''
        ctx.logger.info("basic model does not require training")
        return {
            "status": "success",
            "message": "no training required for basic model"
        }

    def infer(self, ctx) -> pd.DataFrame:
        '''
        run inference and return anomalies as dataframe
        ctx should have: df (dataframe), params (dict), logger
        '''
        ctx.logger.info("executing basic model inference (v2 interface)")

        # get data from context
        df = ctx.df if hasattr(ctx, 'df') else None
        params = ctx.params if hasattr(ctx, 'params') else {}

        if df is None or len(df) == 0:
            ctx.logger.warning("no data provided in context")
            return pd.DataFrame(columns=["entity_id", "entity_type", "risk_score", "anomaly_type", "timestamp", "details"])

        anomalies = []
        row_count = len(df)
        ctx.logger.info(f"processing {row_count} rows")
        
        # basic anomaly detection: flag if row count is suspiciously high
        threshold = params.get("threshold", 10000)
        if row_count > threshold:
            anomalies.append({
                "entity_id": "system",
                "entity_type": "data_volume",
                "risk_score": 0.7,
                "anomaly_type": "high_data_volume",
                "timestamp": pd.Timestamp.now(),
                "details": {
                    "row_count": row_count,
                    "threshold": threshold
                }
            })
        
        # convert to dataframe
        if anomalies:
            return pd.DataFrame(anomalies)
        else:
            return pd.DataFrame(columns=["entity_id", "entity_type", "risk_score", "anomaly_type", "timestamp", "details"])


def _execute_inference(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    '''
    internal inference logic shared by v1 and v2 interfaces
    '''
    logger.info("executing basic model")
    
    # get data source configuration from input
    if not input_data:
        input_data = {}
    
    data_source = input_data.get("data_source") or input_data.get("type", "spark")
    table_name = input_data.get("table_name")
    index_name = input_data.get("index_name")
    file_path = input_data.get("file_path")
    file_name = input_data.get("file_name")
    
    anomalies = []
    df = None
    
    try:
        if data_source == "spark":
            # use spark data adapter
            from core.model_modules.spark.spark import SparkDataLoader
            
            if not table_name:
                raise ValueError("table_name required for spark data source")
            
            loader = SparkDataLoader(table_name=table_name)
            df = loader.data
            
            # basic anomaly detection
            row_count = len(df) if hasattr(df, '__len__') else 0
            logger.info(f"loaded {row_count} rows from spark table: {table_name}")
            
            # example: flag if row count is suspiciously high
            threshold = input_data.get("threshold", 10000)
            if row_count > threshold:
                anomalies.append({
                    "entity_id": "system",
                    "entity_type": "data_volume",
                    "risk_score": 0.7,
                    "anomaly_type": "high_data_volume",
                    "details": {
                        "table_name": table_name,
                        "row_count": row_count,
                        "threshold": threshold
                    }
                })
        
        elif data_source == "elasticsearch":
            # use elasticsearch data adapter
            from core.model_modules.es.es import ESGeneric
            
            if not index_name:
                # try to infer from query or use default
                index_name = input_data.get("index", "openuba-*")
            
            # create query
            query = input_data.get("query", {"match_all": {}})
            es_host = input_data.get("host", os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200"))
            es_loader = ESGeneric(host=es_host, query=query)
            df = es_loader.data
            
            # basic anomaly detection
            if hasattr(df, 'shape') and len(df) > 0:
                row_count = len(df)
                logger.info(f"loaded {row_count} rows from elasticsearch")
                
                # example anomaly detection
                threshold = input_data.get("threshold", 10000)
                if row_count > threshold:
                    anomalies.append({
                        "entity_id": "system",
                        "entity_type": "data_volume",
                        "risk_score": 0.7,
                        "anomaly_type": "high_data_volume",
                        "details": {
                            "index_name": index_name,
                            "document_count": row_count,
                            "threshold": threshold
                        }
                    })
        
        elif data_source == "local_csv":
            # use local pandas csv adapter
            from core.model_modules.local_pandas.local_pandas import LocalPandasCSV
            
            if not file_path or not file_name:
                raise ValueError("file_path and file_name required for local_csv data source")
            
            loader = LocalPandasCSV(
                file_path=file_path,
                file=file_name,
                sep=input_data.get("sep", " "),
                header=input_data.get("header", 0),
                error_bad_lines=False,
                warn_bad_lines=False
            )
            df = loader.data
            
            if hasattr(df, 'shape') and len(df) > 0:
                row_count = len(df)
                logger.info(f"loaded {row_count} rows from local file: {file_name}")
        
        else:
            logger.warning(f"unknown data source: {data_source}")
    
    except Exception as e:
        logger.error(f"model execution failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # return empty result on error
        return {
            "anomalies": [],
            "status": "error",
            "error": str(e)
        }
    
    logger.info(f"model execution completed, found {len(anomalies)} anomalies")
    
    return {
        "anomalies": anomalies,
        "status": "success",
        "anomaly_count": len(anomalies),
        "data_rows_processed": len(df) if df is not None else 0
    }

