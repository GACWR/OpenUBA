'''
Copyright 2019-Present The OpenUBA Platform Authors
elasticsearch integration
'''

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ElasticsearchConnector:
    '''
    connector for elasticsearch
    '''

    def __init__(self, hosts: Optional[List[str]] = None):
        self.hosts = hosts or [os.getenv(
            "ELASTICSEARCH_HOST",
            "http://localhost:9200"
        )]
        self.client = None

    def connect(self):
        '''
        create elasticsearch client
        '''
        try:
            from elasticsearch import Elasticsearch
            self.client = Elasticsearch(
                hosts=self.hosts,
                timeout=60,
                max_retries=3,
                retry_on_timeout=True
            )
            # test connection
            if self.client.ping():
                logger.info(f"connected to elasticsearch: {self.hosts}")
            else:
                raise Exception("elasticsearch ping failed")
        except ImportError:
            logger.warning("elasticsearch library not installed")
            raise
        except Exception as e:
            logger.error(f"failed to connect to elasticsearch: {e}")
            raise

    def index_anomaly(self, anomaly: Dict[str, Any], index: str = "openuba-anomalies"):
        '''
        index an anomaly into elasticsearch
        '''
        if not self.client:
            self.connect()
        try:
            response = self.client.index(
                index=index,
                document=anomaly
            )
            logger.info(f"indexed anomaly: {response['_id']}")
            return response["_id"]
        except Exception as e:
            logger.error(f"failed to index anomaly: {e}")
            raise

    def search_events(
        self,
        query: Dict[str, Any],
        index: str = "openuba-events",
        size: int = 100
    ) -> List[Dict[str, Any]]:
        '''
        search events from elasticsearch
        '''
        if not self.client:
            self.connect()
        try:
            response = self.client.search(
                index=index,
                body={"query": query},
                size=size
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"failed to search events: {e}")
            raise

    def create_index(self, index: str, mapping: Optional[Dict[str, Any]] = None):
        '''
        create an elasticsearch index
        '''
        if not self.client:
            self.connect()
        try:
            if not self.client.indices.exists(index=index):
                body = {}
                if mapping:
                    body["mappings"] = mapping
                self.client.indices.create(index=index, body=body)
                logger.info(f"created index: {index}")
        except Exception as e:
            logger.error(f"failed to create index: {e}")
            raise

    def delete_index(self, index: str):
        '''
        delete an elasticsearch index
        '''
        if not self.client:
            self.connect()
        try:
            if self.client.indices.exists(index=index):
                self.client.indices.delete(index=index)
                logger.info(f"deleted index: {index}")
        except Exception as e:
            logger.error(f"failed to delete index: {e}")
            raise
    
    def bulk_index(
        self,
        documents: List[Dict[str, Any]],
        index: str,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        '''
        bulk index documents into elasticsearch
        '''
        if not self.client:
            self.connect()
        try:
            from elasticsearch.helpers import bulk
            actions = []
            for doc in documents:
                action = {
                    "_index": index,
                    "_source": doc
                }
                if doc_type:
                    action["_type"] = doc_type
                actions.append(action)
            
            success, failed = bulk(
                self.client, 
                actions, 
                raise_on_error=False,
                chunk_size=1000,
                request_timeout=60
            )
            logger.info(f"bulk indexed {success} documents, {len(failed)} failed")
            return {
                "success": success,
                "failed": len(failed),
                "errors": failed
            }
        except Exception as e:
            logger.error(f"failed to bulk index: {e}")
            raise
    
    def get_index_stats(self, index: str) -> Dict[str, Any]:
        '''
        get statistics about an elasticsearch index
        returns document count and size
        '''
        if not self.client:
            self.connect()
        try:
            stats = self.client.indices.stats(index=index)
            index_stats = stats["indices"][index]
            return {
                "index": index,
                "document_count": index_stats["total"]["docs"]["count"],
                "size_bytes": index_stats["total"]["store"]["size_in_bytes"],
                "size_mb": round(index_stats["total"]["store"]["size_in_bytes"] / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"failed to get index stats: {e}")
            raise
    
    def list_indices(self) -> List[str]:
        '''
        list all elasticsearch indices
        '''
        if not self.client:
            self.connect()
        try:
            return list(self.client.indices.get_alias().keys())
        except Exception as e:
            logger.error(f"failed to list indices: {e}")
            return []

    def close(self):
        '''
        close the elasticsearch client
        '''
        if self.client:
            self.client.close()

