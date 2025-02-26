#!/usr/bin/env python
"""Tests for `openapi2callables` package."""

from openapi2callables.parse import parse_spec


def test_parse_spec_basic():
    spec = {
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "operationId": "get_all_users_users_get",
                    "description": "Retrieve a list of all users",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                            "description": "Page number",
                        }
                    ],
                    "responses": {"200": {"description": "Successful response"}},
                }
            }
        }
    }

    expected_result = {
        "get_all_users_users_get": {
            "path": "/users",
            "method": "get",
            "summary": "Get all users",
            "description": "Retrieve a list of all users",
            "parameters": {
                "page": {
                    "_type": "query",
                    "required": False,
                    "type": "integer",
                    "description": "Page number",
                }
            },
            "responses": {"200": {"description": "Successful response"}},
        }
    }

    assert parse_spec(spec) == expected_result
