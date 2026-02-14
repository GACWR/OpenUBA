'''
Copyright 2019-Present The OpenUBA Platform Authors
integrations package
'''

from core.integrations.spark import SparkConnector
from core.integrations.elasticsearch import ElasticsearchConnector

__all__ = [
    "SparkConnector",
    "ElasticsearchConnector",
]

