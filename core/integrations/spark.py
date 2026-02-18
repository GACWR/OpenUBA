'''
Copyright 2019-Present The OpenUBA Platform Authors
apache spark integration
'''

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class SparkConnector:
    '''
    connector for apache spark cluster
    supports both local mode and cluster mode
    '''

    def __init__(
        self,
        master_url: Optional[str] = None,
        app_name: str = "openuba"
    ):
        self.master_url = master_url or os.getenv(
            "SPARK_MASTER_URL",
            "local[*]"
        )
        self.app_name = app_name
        self.spark = None

    def connect(self):
        '''
        create spark session
        '''
        if self.spark:
            return

        try:
            from pyspark.sql import SparkSession
            import socket
            
            # Resolve Pod IP for Driver Host (required for K8s Client Mode)
            try:
                # In K8s, hostname resolves to pod IP or is set in hosts
                host_ip = socket.gethostbyname(socket.gethostname())
                logger.info(f"Resolved driver host IP: {host_ip}")
            except Exception as e:
                logger.warning(f"Could not resolve host IP: {e}")
                host_ip = "0.0.0.0"

            # Auto-configure JAVA_HOME for local Mac dev (Force override if OpenJDK 17 exists)
            # This is necessary because the macOS system Java stub prints "Unable to locate a Java Runtime"
            # if JAVA_HOME is unset or invalid, breaking PySpark's version detection.
            mac_java_paths = [
                "/opt/homebrew/opt/openjdk@17",  # Apple Silicon
                "/usr/local/opt/openjdk@17",     # Intel
            ]
            for mac_java_home in mac_java_paths:
                if os.path.exists(mac_java_home):
                    current_home = os.environ.get("JAVA_HOME")
                    if current_home != mac_java_home:
                        logger.info(f"Forcing JAVA_HOME to {mac_java_home} for local development")
                        os.environ["JAVA_HOME"] = mac_java_home
                    if f"{mac_java_home}/bin" not in os.environ["PATH"]:
                        os.environ["PATH"] = f"{mac_java_home}/bin:{os.environ['PATH']}"
                    break

            # Clean stale Derby lock files from previous crashed sessions
            derby_dir = os.path.join(os.getcwd(), 'metastore', '.derby', 'metastore_db')
            if os.path.isdir(derby_dir):
                for lck in os.listdir(derby_dir):
                    if lck.endswith('.lck'):
                        lck_path = os.path.join(derby_dir, lck)
                        try:
                            os.remove(lck_path)
                        except OSError:
                            pass

            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .master(self.master_url) \
                .config("spark.driver.host", host_ip) \
                .config("spark.driver.bindAddress", "0.0.0.0") \
                .config("spark.driver.extraJavaOptions", f"-Dderby.system.home={os.path.join(os.getcwd(), 'metastore', '.derby')}") \
                .config("spark.sql.warehouse.dir", os.path.join(os.getcwd(), "spark-warehouse")) \
                .config("spark.hadoop.hive.metastore.warehouse.dir", os.path.join(os.getcwd(), "spark-warehouse")) \
                .config("spark.hadoop.javax.jdo.option.ConnectionURL", f"jdbc:derby:{os.path.join(os.getcwd(), 'metastore', '.derby', 'metastore_db')};create=true") \
                .config("spark.driver.memory", "512m") \
                .config("spark.executor.memory", "512m") \
                .enableHiveSupport() \
                .getOrCreate()
            logger.info(f"connected to spark: {self.master_url}")
        except ImportError:
            logger.warning("pyspark not installed, spark integration unavailable")
        except Exception as e:
            # catch java gateway errors (missing java)
            logger.error(f"failed to connect to spark: {e}")
            self.spark = None

    def read_data(self, path: str, format: str = "parquet", **options):
        '''
        read data from spark data source
        '''
        if not self.spark:
            self.connect()
        
        if not self.spark:
            logger.warning("spark not available, cannot read data")
            return None

        if format == "parquet":
            return self.spark.read.parquet(path)
        elif format == "csv":
            return self.spark.read.csv(
                path,
                header=options.get("header", True),
                inferSchema=options.get("inferSchema", True),
                sep=options.get("sep", ","),
                encoding=options.get("encoding", "UTF-8")
            )
        elif format == "json":
            return self.spark.read.json(path)
        else:
            raise ValueError(f"unsupported format: {format}")
    
    def write_data(self, dataframe, path: str, format: str = "parquet", mode: str = "overwrite"):
        '''
        write dataframe to spark data source
        '''
        if not self.spark:
            self.connect()
        
        if not self.spark:
            logger.warning("spark not available, cannot write data")
            return

        if format == "parquet":
            dataframe.write.mode(mode).parquet(path)
        elif format == "csv":
            dataframe.write.mode(mode).csv(path, header=True)
        else:
            raise ValueError(f"unsupported format: {format}")
        logger.info(f"wrote data to {path} in {format} format")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        '''
        get information about a spark table
        '''
        if not self.spark:
            self.connect()
        
        if not self.spark:
            return {}

        try:
            df = self.spark.table(table_name)
            row_count = df.count()
            schema = df.schema.json()
            return {
                "table_name": table_name,
                "row_count": row_count,
                "schema": schema
            }
        except Exception as e:
            logger.error(f"failed to get table info: {e}")
            raise
    
    def list_tables(self) -> List[str]:
        '''
        list all tables in spark catalog
        '''
        if not self.spark:
            self.connect()
        
        if not self.spark:
            return []

        try:
            tables = self.spark.catalog.listTables()
            return [table.name for table in tables]
        except Exception as e:
            logger.error(f"failed to list tables: {e}")
            return []

    def submit_job(self, job_config: Dict[str, Any]) -> str:
        '''
        submit a spark job
        '''
        if not self.spark:
            self.connect()
        
        if not self.spark:
            logger.warning("spark not available, cannot submit job")
            return "job_submission_failed"

        # placeholder for job submission logic
        logger.info(f"submitting spark job: {job_config}")
        return "job_id_placeholder"

    def close(self):
        '''
        close spark session
        '''
        if self.spark:
            self.spark.stop()
            self.spark = None
            logger.info("spark session closed")

