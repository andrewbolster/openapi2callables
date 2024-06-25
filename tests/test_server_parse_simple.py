#!/usr/bin/env python
"""
Tests for `openapi2tools.parse` package, on 'live' OpenAPI specs from `openapi2tools.server`
"""
import pytest
from fastapi.testclient import TestClient
from openapi2tools.parse import parse_spec
from openapi2tools.server import app


@pytest.fixture
def client():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return TestClient(app)


@pytest.fixture
def schema(client):
    response = client.get("/openapi.json")
    return response.json()


def test_parse_spec_basic(schema):
    tools = parse_spec(schema)

    expected_result = {
        "path": "/pirate",
        "method": "get",
        "summary": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "description": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "parameters": {},
        "responses": {"200": {"description": "Successful response"}},
    }

    assert "pirate_endpoint_pirate_get" in tools
    assert tools["pirate_endpoint_pirate_get"]["path"] == "/pirate"
    assert tools["pirate_endpoint_pirate_get"]["parameters"] == {}
