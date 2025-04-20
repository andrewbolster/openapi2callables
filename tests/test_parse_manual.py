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
            "tags": [],
            "deprecated": False,
        }
    }

    result = parse_spec(spec)
    assert result == expected_result


def test_parse_spec_nested_objects():
    spec = {
        "paths": {
            "/create_ship": {
                "post": {
                    "summary": "Create a ship",
                    "operationId": "create_ship_post",
                    "description": "Create a new ship with nested details",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "details": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string"},
                                                "capacity": {"type": "integer"},
                                            },
                                            "required": ["type"],
                                        },
                                    },
                                    "required": ["name"],
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Ship created"}},
                }
            }
        }
    }

    result = parse_spec(spec)
    assert "create_ship_post" in result
    assert result["create_ship_post"]["parameters"]["details"]["type"]["type"] == "object"


def test_parse_spec_enums():
    spec = {
        "paths": {
            "/update_rank": {
                "put": {
                    "summary": "Update pirate rank",
                    "operationId": "update_rank_put",
                    "description": "Update the rank of a pirate",
                    "parameters": [
                        {
                            "name": "rank",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "enum": ["captain", "first_mate"]},
                        }
                    ],
                    "responses": {"200": {"description": "Rank updated"}},
                }
            }
        }
    }

    result = parse_spec(spec)
    assert "update_rank_put" in result
    assert result["update_rank_put"]["parameters"]["rank"]["enum"] == ["captain", "first_mate"]
