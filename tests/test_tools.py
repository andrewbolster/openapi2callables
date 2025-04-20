from unittest.mock import Mock

import pytest

from openapi2callables.tools import APITool, LocalTool


def test_tool_to_tool_spec():
    tool = LocalTool(
        operationId="test_tool",
        description="A test tool",
        parameters={
            "param1": {"type": "string", "description": "A string parameter", "required": True},
            "param2": {"type": "integer", "description": "An integer parameter", "required": False},
        },
    )
    spec = tool.to_tool_spec()
    assert spec["function"]["name"] == "test_tool"
    assert "param1" in spec["function"]["parameters"]["properties"]
    assert "param2" in spec["function"]["parameters"]["properties"]


def test_local_tool_call():
    tool = LocalTool(
        operationId="add",
        description="Add two numbers",
        parameters={"x": {"type": "integer", "description": "First number", "required": True}},
        func=lambda x: x + 1,
    )
    assert tool(1) == 2


def test_api_tool_requires_auth():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
        access_token_name="api_key",
    )
    assert tool.requires_auth is True


def test_api_tool_resolve_access_token():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
        access_token_name="api_key",
        access_token="test_token",
    )
    assert tool.resolve_access_token({}) == "test_token"


def test_api_tool_validate_parameter_type():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={"param1": {"type": "integer"}},
    )
    tool.validate_parameter_type("param1", 123)  # Should not raise an error
    with pytest.raises(TypeError):
        tool.validate_parameter_type("param1", "not an integer")


def test_api_tool_prepare_request_data():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        path="/test/{id}",
        parameters={
            "id": {"_type": "path", "type": "integer", "required": True},
            "query_param": {"_type": "query", "type": "string", "required": False},
        },
    )
    path, params, headers, cookies, body, files = tool.prepare_request_data({"id": 1, "query_param": "test"})
    assert path == "/test/1"
    assert params == {"query_param": "test"}


def test_api_tool_handle_response():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
    )
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    assert tool.handle_response(mock_response) == {"key": "value"}


def test_api_tool_call():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        base_url="http://example.com",
        path="/test",
        method="get",
        parameters={},
    )
    mock_client = Mock()
    mock_client.return_value.status_code = 200
    mock_client.return_value.json.return_value = {"success": True}
    response = tool(client=mock_client)
    assert response == {"success": True}


def test_tool_requires_confirmation():
    tool = LocalTool(
        operationId="test_tool",
        description="A test tool",
        parameters={},
        tags={"requires-confirmation"},
    )
    assert tool.requires_confirmation is True


def test_tool_to_tool_spec_with_required_params():
    tool = LocalTool(
        operationId="test_tool",
        description="A test tool",
        parameters={
            "param1": {"type": "string", "description": "A string parameter", "required": True},
            "param2": {"type": "integer", "description": "An integer parameter", "required": False},
        },
    )
    spec = tool.to_tool_spec()
    assert spec["function"]["parameters"]["required"] == ["param1"]


def test_api_tool_post_init_with_access_token():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
        access_token_name="api_key",
    )
    assert "api_key" in tool.parameters
    assert tool.parameters["api_key"]["description"].endswith("NEVER ask a user for this!)")


def test_api_tool_requires_auth_with_security_schemes():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
        security_schemes={"apiKeyAuth": {"type": "apiKey"}},
    )
    assert tool.requires_auth is True


def test_api_tool_resolve_access_token_priority():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
        access_token_name="api_key",
        access_token="default_token",
    )
    assert tool.resolve_access_token({"api_key": "runtime_token"}) == "runtime_token"
    assert tool.resolve_access_token({}) == "default_token"


def test_api_tool_validate_parameter_type_edge_cases():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={"param1": {"type": ["integer", "string"]}},
    )
    tool.validate_parameter_type("param1", 123)  # Should not raise an error
    tool.validate_parameter_type("param1", "test")  # Should not raise an error
    with pytest.raises(TypeError):
        tool.validate_parameter_type("param1", 12.34)


def test_api_tool_prepare_request_data_with_all_types():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        path="/test/{id}",
        parameters={
            "id": {"_type": "path", "type": "integer", "required": True},
            "query_param": {"_type": "query", "type": "string", "required": False},
            "header_param": {"_type": "header", "type": "string", "required": False},
            "cookie_param": {"_type": "cookie", "type": "string", "required": False},
            "body_param": {"_type": "body", "type": "object", "required": False},
        },
    )
    path, params, headers, cookies, body, files = tool.prepare_request_data(
        {
            "id": 1,
            "query_param": "test",
            "header_param": "header",
            "cookie_param": "cookie",
            "body_param": {"key": "value"},
        }
    )
    assert path == "/test/1"
    assert params == {"query_param": "test"}
    assert headers == {"header_param": "header"}
    assert cookies == {"cookie_param": "cookie"}
    assert body == {"body_param": {"key": "value"}}


def test_api_tool_handle_response_error():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        parameters={},
    )
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    result = tool.handle_response(mock_response)
    assert result["error"] is True
    assert result["status_code"] == 400


def test_api_tool_call_with_mock_client():
    tool = APITool(
        operationId="test_api",
        description="Test API tool",
        base_url="http://example.com",
        path="/test",
        method="post",
        parameters={"param1": {"_type": "body", "type": "string", "required": True}},
    )
    mock_client = Mock()
    mock_client.return_value.status_code = 200
    mock_client.return_value.json.return_value = {"success": True}
    response = tool(client=mock_client, param1="value")
    assert response == {"success": True}
