from unittest.mock import patch

import pytest
import requests

from openapi2callables.parse import extract_constraints, extract_type_from_schema, get_spec, parse_spec


def test_get_spec_invalid_path():
    with pytest.raises(ValueError, match="File not found"):
        get_spec("non_existent_file.yaml")


def test_get_spec_invalid_url():
    with pytest.raises(ValueError, match="Could not fetch spec from URL"):
        get_spec("http://invalid-url.com/openapi.json")


def test_get_spec_unsupported_extension():
    with patch("os.path.exists", return_value=True):
        with pytest.raises(ValueError, match="Unsupported file type"):
            get_spec("unsupported_file.txt")


def test_parse_spec_empty_spec():
    spec = {}
    with pytest.raises(KeyError, match="'paths'"):
        parse_spec(spec)


def test_parse_spec_missing_fields():
    spec = {"paths": {}}
    result = parse_spec(spec)
    assert result == {}


def test_parse_spec_deprecated_operations():
    spec = {
        "paths": {
            "/deprecated": {
                "get": {
                    "deprecated": True,
                    "operationId": "deprecated_get",
                }
            }
        }
    }
    result = parse_spec(spec, include_deprecated=False)
    assert "deprecated_get" not in result


def test_extract_type_from_schema_nested_objects():
    schema = {
        "type": "object",
        "properties": {"nested": {"type": "object", "properties": {"field": {"type": "string"}}}},
    }
    result = extract_type_from_schema(schema)
    assert result["type"] == "object"
    assert "nested" in result["properties"]


def test_extract_constraints_string():
    schema = {"type": "string", "minLength": 5, "maxLength": 10, "pattern": "^[a-z]+$"}
    result = extract_constraints(schema)
    assert result == {"minLength": 5, "maxLength": 10, "pattern": "^[a-z]+$"}


def test_extract_constraints_numeric():
    schema = {"type": "integer", "minimum": 1, "maximum": 100, "multipleOf": 5}
    result = extract_constraints(schema)
    assert result == {"minimum": 1, "maximum": 100, "multipleOf": 5}


def test_parse_spec_security():
    spec = {
        "paths": {
            "/secure": {
                "get": {
                    "operationId": "secure_get",
                    "security": [{"apiKeyAuth": []}],
                }
            }
        },
        "components": {"securitySchemes": {"apiKeyAuth": {"type": "apiKey", "name": "X-API-KEY", "in": "header"}}},
    }
    result = parse_spec(spec)
    assert "secure_get" in result
    assert result["secure_get"]["security"] == [{"apiKeyAuth": []}]


def test_get_spec_valid_local_yaml(tmp_path):
    yaml_file = tmp_path / "spec.yaml"
    yaml_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\npaths: {}")
    spec = get_spec(str(yaml_file))
    assert spec["openapi"] == "3.0.0"


def test_get_spec_connection_failure():
    with patch("requests.get", side_effect=requests.RequestException("Connection error")):
        with pytest.raises(ValueError, match="Could not fetch spec from URL"):
            get_spec("http://invalid-url.com/spec.json")


def test_parse_spec_with_deprecated_operations():
    spec = {
        "paths": {
            "/deprecated": {
                "get": {
                    "operationId": "deprecated_get",
                    "deprecated": True,
                }
            }
        }
    }
    result = parse_spec(spec, include_deprecated=True)
    assert "deprecated_get" in result


def test_parse_spec_with_security():
    spec = {
        "paths": {
            "/secure": {
                "get": {
                    "operationId": "secure_get",
                    "security": [{"apiKeyAuth": []}],
                }
            }
        },
        "components": {
            "securitySchemes": {
                "apiKeyAuth": {
                    "type": "apiKey",
                    "name": "X-API-KEY",
                    "in": "header",
                }
            }
        },
    }
    result = parse_spec(spec)
    assert "secure_get" in result
    assert result["secure_get"]["security"] == [{"apiKeyAuth": []}]


def test_parse_spec_with_complex_request_body():
    spec = {
        "paths": {
            "/complex": {
                "post": {
                    "operationId": "complex_post",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "nested": {
                                            "type": "object",
                                            "properties": {"field": {"type": "string"}},
                                        },
                                        "array": {"type": "array", "items": {"type": "integer"}},
                                    },
                                }
                            }
                        }
                    },
                }
            }
        }
    }
    result = parse_spec(spec)
    assert "complex_post" in result
    assert result["complex_post"]["parameters"]["nested"]["type"]["type"] == "object"
    assert result["complex_post"]["parameters"]["array"]["type"]["type"] == "array"


def test_extract_type_from_schema_with_anyof():
    schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    result = extract_type_from_schema(schema)
    assert result == ["string", "integer"]


def test_extract_type_from_schema_with_ref():
    schema = {"$ref": "#/components/schemas/Example"}
    result = extract_type_from_schema(schema)
    assert result == "Example"


def test_extract_constraints_with_minimum_and_maximum():
    schema = {"type": "integer", "minimum": 1, "maximum": 10}
    result = extract_constraints(schema)
    assert result == {"minimum": 1, "maximum": 10}
