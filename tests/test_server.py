#!/usr/bin/env python
"""
Tests for `openapi2callables.server` package.

These are predominatly to 'lock-down' expected types etc from the server to then align the real capabilities of the package in `test_parse.py`
"""

import pytest
from fastapi.testclient import TestClient

from openapi2callables.server import app


@pytest.fixture
def client():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return TestClient(app)


def test_pirate_endpoint(client):
    response = client.get("/get_pirate")
    assert response.status_code == 200
    assert response.text == '"Arr, matey! Welcome to the pirate endpoint!"'


def test_pirate_endpoint_with_name(client):
    name = "Jack Sparrow"
    response = client.get(f"/urlparam_pirate/{name}")
    assert response.status_code == 200
    assert response.text == f'"Arr, matey! Welcome to the pirate endpoint, {name}!"'


def test_pirate_endpoint_body(client):
    name = "Blackbeard"
    response = client.post("/post_pirate", json={"name": name})
    assert response.status_code == 200
    assert response.text == f'"Arr, matey! Welcome to the pirate endpoint, {name}!"'
