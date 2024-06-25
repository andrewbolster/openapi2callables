#!/usr/bin/env python
"""
Tests for `openapi2tools.server` package.

These are predominatly to 'lock-down' expected types etc from the server to then align the real capabilities of the package in `test_parse.py`
"""
import pytest
from fastapi.testclient import TestClient
from openapi2tools.server import app


@pytest.fixture
def client():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return TestClient(app)


def test_pirate_endpoint(client):
    response = client.get("/pirate")
    assert response.status_code == 200
    assert response.text == '"Arr, matey! Welcome to the pirate endpoint!"'


def test_pirate_endpoint_with_no_name(client):
    response = client.get("/pirate")
    assert response.status_code == 200
    assert response.text == '"Arr, matey! Welcome to the pirate endpoint!"'


def test_pirate_endpoint_with_name(client):
    name = "Jack Sparrow"
    response = client.get(f"/pirate/{name}")
    assert response.status_code == 200
    assert response.text == f'"Arr, matey! Welcome to the pirate endpoint, {name}!"'
