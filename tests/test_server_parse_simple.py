#!/usr/bin/env python
"""
Tests for `openapi2callables.parse` package, on 'live' OpenAPI specs from `openapi2callables.server`
"""

import pytest
from fastapi.testclient import TestClient

from openapi2callables import APITool
from openapi2callables.parse import parse_spec
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


@pytest.mark.parametrize(
    "operation_id, params, expected_response",
    [
        # Test GET with no parameters
        ("pirate_endpoint_get_pirate_get", {}, "Arr, matey! Welcome to the pirate endpoint!"),
        # Test GET with path parameter
        (
            "pirate_endpoint_name_urlparam_pirate__name__get",
            {"name": "Jack Sparrow"},
            "Arr, matey! Welcome to the pirate endpoint, Jack Sparrow!",
        ),
        # Test POST with body parameter
        (
            "pirate_endpoint_body_post_pirate_post",
            {"name": "Blackbeard"},
            "Arr, matey! Welcome to the pirate endpoint, Blackbeard!",
        ),
    ],
)
def test_api_tool(client, schema, operation_id, params, expected_response):
    tools = parse_spec(schema)
    tool = tools[operation_id]
    api_tool = APITool(operationId=operation_id, base_url=client.base_url, **tool)

    result = api_tool(client=client.request, **params)
    assert result == expected_response


@pytest.mark.parametrize(
    "operation_id, params, expected_error",
    [
        # Missing required parameter
        ("pirate_endpoint_name_urlparam_pirate__name__get", {}, ValueError),
        # Invalid parameter type
        ("pirate_endpoint_body_post_pirate_post", {"name": 123}, TypeError),
    ],
)
def test_api_tool_errors(client, schema, operation_id, params, expected_error):
    tools = parse_spec(schema)
    tool = tools[operation_id]
    api_tool = APITool(operationId=operation_id, base_url=client.base_url, **tool)

    with pytest.raises(expected_error):
        api_tool(client=client.request, **params)


def test_parse_spec_get(schema):
    operationId = "pirate_endpoint_get_pirate_get"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/get_pirate",
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
    operationId = "pirate_endpoint_get_pirate_get"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    result = api_tool(client=client.request)
    assert result == "Arr, matey! Welcome to the pirate endpoint!"


def test_parse_spec_get_name_param(schema):
    operationId = "pirate_endpoint_name_urlparam_pirate__name__get"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/urlparam_pirate/{name}",
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


def test_execute_spec_get_name_param(client, schema):
    tools = parse_spec(schema)
    operationId = "pirate_endpoint_name_urlparam_pirate__name__get"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    result = api_tool(client=client.request, name="Jack Sparrow")
    assert result == "Arr, matey! Welcome to the pirate endpoint, Jack Sparrow!"


def test_parse_spec_post(schema):
    operationId = "pirate_endpoint_body_post_pirate_post"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/post_pirate",
        "method": "post",
        "summary": "Pirate endpoint. Simplest possible endpoint; Post Body input, only string response",
        "description": "Pirate endpoint. Simplest possible endpoint; Post Body input, only string response",
        "parameters": {
            "name": {
                "_type": "body",
                "required": True,
                "type": "string",
                "description": "",
            },
            "age": {
                "_type": "body",
                "required": False,
                "type": ["integer"],
                "description": "",
            },
            "ship": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "rank": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "joined_date": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "skills": {
                "_type": "body",
                "required": False,
                "type": {"items": "string", "type": "array"},
                "description": "",
            },
            "bounty": {
                "_type": "body",
                "required": False,
                "type": ["number"],
                "description": "",
            },
            "is_active": {
                "_type": "body",
                "required": False,
                "type": "boolean",
                "description": "",
            },
        },
        "responses": {"200": {"description": "Successful response"}},
        "tags": [],
        "deprecated": False,
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]


def test_execute_spec_post(client, schema):
    tools = parse_spec(schema)
    operationId = "pirate_endpoint_body_post_pirate_post"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    result = api_tool(client=client.request, name="Blackbeard")
    assert result == "Arr, matey! Welcome to the pirate endpoint, Blackbeard!"


def test_parse_spec_put(schema):
    operationId = "update_pirate_update_pirate__name__put"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/update_pirate/{name}",
        "method": "put",
        "summary": "Update a pirate's information.",
        "description": "Update a pirate's information.",
        "parameters": {
            "name": {
                "_type": "path",
                "required": True,
                "type": "string",
                "description": "",
            },
            "name_body": {  # Recover from _body naming collision in parse_spec
                "_type": "body",
                "required": True,
                "type": "string",
                "description": "",
            },
            "age": {
                "_type": "body",
                "required": False,
                "type": ["integer"],
                "description": "",
            },
            "ship": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "rank": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "joined_date": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "skills": {
                "_type": "body",
                "required": False,
                "type": {"items": "string", "type": "array"},
                "description": "",
            },
            "bounty": {
                "_type": "body",
                "required": False,
                "type": ["number"],
                "description": "",
            },
            "is_active": {
                "_type": "body",
                "required": False,
                "type": "boolean",
                "description": "",
            },
        },
        "responses": {"200": {"description": "Successful response"}},
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]


def test_execute_spec_put(client, schema):
    tools = parse_spec(schema)
    operationId = "update_pirate_update_pirate__name__put"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    # First, add a pirate to update
    client.post("/add_pirate", json={"name": "Jack", "age": 30, "ship": "Black Pearl"})

    result = api_tool(client=client.request, name="Jack", age=35, ship="Flying Dutchman")
    assert result == "Pirate Jack updated!"


def test_parse_spec_delete(schema):
    operationId = "delete_pirate_delete_pirate__name__delete"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/delete_pirate/{name}",
        "method": "delete",
        "summary": "Delete a pirate.",
        "description": "Delete a pirate.",
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


def test_execute_spec_delete(client, schema):
    tools = parse_spec(schema)
    operationId = "delete_pirate_delete_pirate__name__delete"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    # First, add a pirate to delete
    client.post("/add_pirate", json={"name": "Jack", "age": 30, "ship": "Black Pearl"})

    result = api_tool(client=client.request, name="Jack")
    assert result == "Pirate Jack deleted!"


def test_parse_spec_search(schema):
    operationId = "search_pirates_search_pirates_get"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/search_pirates",
        "method": "get",
        "summary": "Search pirates by ship.",
        "description": "Search pirates by ship.",
        "parameters": {
            "ship": {
                "_type": "query",
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


def test_execute_spec_search(client, schema):
    tools = parse_spec(schema)
    operationId = "search_pirates_search_pirates_get"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    # First, add a pirate to search
    client.post("/add_pirate", json={"name": "Jack", "age": 30, "ship": "Black Pearl"})

    result = api_tool(client=client.request, ship="Black Pearl")
    # Assert that _at least_ the configured fields appear in the result
    assert len(result) > 0
    in_result = False
    for pirate in result:
        if pirate["name"] == "Jack" and pirate["age"] == 30 and pirate["ship"] == "Black Pearl":
            in_result = True
            break
    assert in_result, "Expected pirate not found in the result"


def test_parse_spec_get_all(schema):
    operationId = "get_pirates_get_pirates_get"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/get_pirates",
        "method": "get",
        "summary": "Get all pirates.",
        "description": "Get all pirates.",
        "parameters": {},
        "responses": {"200": {"description": "Successful response"}},
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]


def test_execute_spec_get_all(client, schema):
    tools = parse_spec(schema)
    operationId = "get_pirates_get_pirates_get"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    # First, add a pirate to get
    client.post("/add_pirate", json={"name": "Jack", "age": 30, "ship": "Black Pearl"})

    result = api_tool(client=client.request)
    # Assert that _at least_ the configured fields appear in the result
    assert len(result) > 0
    in_result = False
    for pirate in result:
        if pirate["name"] == "Jack" and pirate["age"] == 30 and pirate["ship"] == "Black Pearl":
            in_result = True
            break
    assert in_result, "Expected pirate not found in the result"


def test_parse_spec_add(schema):
    operationId = "add_pirate_add_pirate_post"
    tools = parse_spec(schema)

    expected_result = {
        "path": "/add_pirate",
        "method": "post",
        "summary": "Add a new pirate.",
        "description": "Add a new pirate.",
        "parameters": {
            "name": {
                "_type": "body",
                "required": True,
                "type": "string",
                "description": "",
            },
            "age": {
                "_type": "body",
                "required": False,
                "type": ["integer"],
                "description": "",
            },
            "ship": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "rank": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "joined_date": {
                "_type": "body",
                "required": False,
                "type": ["string"],
                "description": "",
            },
            "skills": {
                "_type": "body",
                "required": False,
                "type": {"items": "string", "type": "array"},
                "description": "",
            },
            "bounty": {
                "_type": "body",
                "required": False,
                "type": ["number"],
                "description": "",
            },
            "is_active": {
                "_type": "body",
                "required": False,
                "type": "boolean",
                "description": "",
            },
        },
        "responses": {"200": {"description": "Successful response"}},
    }

    assert operationId in tools
    assert tools[operationId]["path"] == expected_result["path"]
    assert tools[operationId]["parameters"] == expected_result["parameters"]


def test_execute_spec_add(client, schema):
    tools = parse_spec(schema)
    operationId = "add_pirate_add_pirate_post"
    tool = tools[operationId]
    api_tool = APITool(operationId=operationId, base_url=client.base_url, **tool)

    result = api_tool(client=client.request, name="Jack", age=30, ship="Black Pearl")
    assert result == "Pirate Jack added!"
