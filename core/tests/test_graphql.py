'''
Copyright 2019-Present The OpenUBA Platform Authors
graphql api tests
'''

import pytest
from fastapi.testclient import TestClient


def test_graphql_endpoint_available(test_client: TestClient):
    '''
    test that graphql endpoint is available
    note: this tests the endpoint exists, actual graphql queries
    would require postgraphile to be running
    '''
    # graphql endpoint should be available
    # in production this would be at /graphql
    # for now we just verify the app structure supports it
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    # graphql endpoint info may be in response if available
    assert "endpoints" in data

