'''
Copyright 2019-Present The OpenUBA Platform Authors
database utilities for e2e testing
'''

import os
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DBTestUtils:
    '''
    utilities for database verification in e2e tests
    '''

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            # try to get from environment or use default
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://openuba:openuba@localhost:5432/openuba"
            )
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        '''
        get database session context manager
        '''
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def query_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        '''
        query model by id
        '''
        with self.get_session() as session:
            result = session.execute(
                text("SELECT * FROM models WHERE id::text = :id"),
                {"id": str(model_id)}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def query_anomaly(self, anomaly_id: str) -> Optional[Dict[str, Any]]:
        '''
        query anomaly by id
        '''
        with self.get_session() as session:
            result = session.execute(
                text("SELECT * FROM anomalies WHERE id::text = :id"),
                {"id": str(anomaly_id)}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def query_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        '''
        query case by id
        '''
        with self.get_session() as session:
            result = session.execute(
                text("SELECT * FROM cases WHERE id::text = :id"),
                {"id": str(case_id)}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def query_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        '''
        query rule by id
        '''
        with self.get_session() as session:
            result = session.execute(
                text("SELECT * FROM rules WHERE id::text = :id"),
                {"id": str(rule_id)}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def count_models(self) -> int:
        '''
        count total models
        '''
        with self.get_session() as session:
            result = session.execute(text("SELECT COUNT(*) FROM models"))
            return result.scalar() or 0

    def count_anomalies(self, filters: Optional[Dict[str, Any]] = None) -> int:
        '''
        count anomalies with optional filters
        '''
        query = "SELECT COUNT(*) FROM anomalies WHERE 1=1"
        params = {}
        if filters:
            if "model_id" in filters:
                query += " AND model_id = :model_id"
                params["model_id"] = filters["model_id"]
            if "acknowledged" in filters:
                query += " AND acknowledged = :acknowledged"
                params["acknowledged"] = filters["acknowledged"]

        with self.get_session() as session:
            result = session.execute(text(query), params)
            return result.scalar() or 0

    def count_cases(self, status: Optional[str] = None) -> int:
        '''
        count cases, optionally filtered by status
        '''
        query = "SELECT COUNT(*) FROM cases"
        params = {}
        if status:
            query += " WHERE status = :status"
            params["status"] = status
        else:
            query += " WHERE 1=1"

        with self.get_session() as session:
            result = session.execute(text(query), params)
            return result.scalar() or 0

    def get_case_anomalies(self, case_id: str) -> List[Dict[str, Any]]:
        '''
        get anomalies linked to a case
        '''
        with self.get_session() as session:
            result = session.execute(
                text("""
                    SELECT a.* FROM anomalies a
                    INNER JOIN case_anomalies ca ON a.id = ca.anomaly_id
                    WHERE ca.case_id::text = :case_id
                """),
                {"case_id": str(case_id)}
            )
            return [dict(row._mapping) for row in result]

    def get_execution_logs(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        get execution logs, optionally filtered by model_id
        '''
        query = "SELECT * FROM execution_logs"
        params = {}
        if model_id:
            query += " WHERE model_id = :model_id"
            params["model_id"] = model_id
        query += " ORDER BY started_at DESC"

        with self.get_session() as session:
            result = session.execute(text(query), params)
            result = session.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    def get_model_runs(self, model_version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        get model runs/jobs, optionally filtered by model_version_id
        '''
        query = "SELECT * FROM model_runs"
        params = {}
        if model_version_id:
            query += " WHERE model_version_id = :model_version_id"
            params["model_version_id"] = model_version_id
        query += " ORDER BY created_at DESC"

        with self.get_session() as session:
            result = session.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    def get_model_versions(self, model_id: str) -> List[Dict[str, Any]]:
        '''
        get versions for a model
        '''
        query = "SELECT * FROM model_versions WHERE model_id = :model_id ORDER BY installed_at DESC"
        with self.get_session() as session:
            result = session.execute(text(query), {"model_id": model_id})
            return [dict(row._mapping) for row in result]

    def get_data_ingestion_runs(self, dataset_name: Optional[str] = None) -> List[Dict[str, Any]]:
        '''
        get data ingestion runs
        '''
        query = "SELECT * FROM data_ingestion_runs"
        params = {}
        if dataset_name:
            query += " WHERE dataset_name = :dataset_name"
            params["dataset_name"] = dataset_name
        query += " ORDER BY created_at DESC"
        
        with self.get_session() as session:
            result = session.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    def verify_model_exists(self, model_id: str) -> bool:
        '''
        verify model exists in database
        '''
        return self.query_model(model_id) is not None

    def verify_anomaly_exists(self, anomaly_id: str) -> bool:
        '''
        verify anomaly exists in database
        '''
        return self.query_anomaly(anomaly_id) is not None

    def verify_case_exists(self, case_id: str) -> bool:
        '''
        verify case exists in database
        '''
        return self.query_case(case_id) is not None

    def query_generic(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        '''
        query any table by id
        '''
        with self.get_session() as session:
            result = session.execute(
                text(f"SELECT * FROM {table} WHERE id::text = :id"),
                {"id": str(record_id)}
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def count_table(self, table: str, where_clause: str = "1=1", params: Optional[Dict] = None) -> int:
        '''
        count rows in any table with optional where clause
        '''
        with self.get_session() as session:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"), params or {})
            return result.scalar() or 0

    def table_exists(self, table: str) -> bool:
        '''
        check if a table exists in the database
        '''
        with self.get_session() as session:
            result = session.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table)"),
                {"table": table}
            )
            return result.scalar()

    def cleanup_test_data(self, test_prefix: str = "e2e_test_"):
        '''
        cleanup test data with given prefix
        this is a safety measure - be careful with this
        '''
        logger.warning(f"cleaning up test data with prefix: {test_prefix}")
        with self.get_session() as session:
            # cleanup new platform tables first (they have no FK deps on old tables)
            new_tables_by_name = [
                ("pipeline_runs", "pipeline_id IN (SELECT id FROM pipelines WHERE name LIKE :prefix)"),
                ("pipelines", "name LIKE :prefix"),
                ("experiment_runs", "experiment_id IN (SELECT id FROM experiments WHERE name LIKE :prefix)"),
                ("experiments", "name LIKE :prefix"),
                ("hyperparameter_sets", "name LIKE :prefix"),
                ("features", "group_id IN (SELECT id FROM feature_groups WHERE name LIKE :prefix)"),
                ("feature_groups", "name LIKE :prefix"),
                ("visualizations", "name LIKE :prefix"),
                ("dashboards", "name LIKE :prefix"),
                ("job_logs", "job_id IN (SELECT id FROM jobs WHERE name LIKE :prefix)"),
                ("training_metrics", "job_id IN (SELECT id FROM jobs WHERE name LIKE :prefix)"),
                ("jobs", "name LIKE :prefix"),
                ("workspaces", "name LIKE :prefix"),
                ("datasets", "name LIKE :prefix"),
            ]
            for table, condition in new_tables_by_name:
                try:
                    session.execute(text(f"DELETE FROM {table} WHERE {condition}"), {"prefix": f"{test_prefix}%"})
                except Exception:
                    pass  # table may not exist yet

            # delete in order to respect foreign keys (original tables)
            session.execute(
                text("DELETE FROM case_anomalies WHERE case_id IN (SELECT id FROM cases WHERE title LIKE :prefix)"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM user_feedback WHERE anomaly_id IN (SELECT id FROM anomalies WHERE entity_id LIKE :prefix)"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM anomalies WHERE entity_id LIKE :prefix"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM cases WHERE title LIKE :prefix"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM execution_logs WHERE model_id IN (SELECT id FROM models WHERE name LIKE :prefix)"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM anomalies WHERE model_id IN (SELECT id FROM models WHERE name LIKE :prefix)"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM models WHERE name LIKE :prefix"),
                {"prefix": f"{test_prefix}%"}
            )
            session.execute(
                text("DELETE FROM rules WHERE name LIKE :prefix"),
                {"prefix": f"{test_prefix}%"}
            )
            session.commit()

