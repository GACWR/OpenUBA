'''
Copyright 2019-Present The OpenUBA Platform Authors
graphql package
'''

from core.graphql.postgraphile import (
    PostGraphileServer,
    get_graphql_url,
    get_graphiql_url
)

__all__ = [
    "PostGraphileServer",
    "get_graphql_url",
    "get_graphiql_url",
]

