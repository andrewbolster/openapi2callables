#!/usr/bin/env python
"""
Tests for `openapi2callables.parse` package, on 'live' OpenAPI specs from `openapi2callables.server`
"""

import pytest
from fastapi.testclient import TestClient
from openapi2callables.parse import parse_spec, APITool
from openapi2callables.server import app


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


def test_parse_spec_get(schema):
    operationId = "pirate_endpoint_pirate_get"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/pirate",
        "method": "get",
        "summary": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "description": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "parameters": {},
        "responses": {"200": {"description": "Successful response"}},
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]


def test_execute_spec_get(client, schema):
    tools = parse_spec(schema)
    operationId = "pirate_endpoint_pirate_get"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    result = api_tool(client=client.request)
    assert result == "Arr, matey! Welcome to the pirate endpoint!"


def test_parse_spec_get_name_param(schema):
    operationId = "pirate_endpoint_pirate__name__get"
    tools = parse_spec(schema)

    expected_result = {
        "path":  "/pirate/{name}",
        "method": "get",
        "summary": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "description": "Pirate endpoint. Simplest possible endpoint; no inputs, only string response",
        "parameters": {
        "name": {
            "_type": "path",
            "required": True,
            "type": "string",
            "description": "",
        }
    },
        "responses": {"200": {"description": "Successful response"}},
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]
