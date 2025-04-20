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


def test_create_ship_valid_api_key(client):
    response = client.post(
        "/ships",
        json={"name": "Black Pearl", "type": "Galleon", "capacity": 100, "cannons": 20},
        headers={"X-API-KEY": "test-api-key"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Black Pearl"


def test_create_ship_invalid_api_key(client):
    response = client.post(
        "/ships",
        json={"name": "Flying Dutchman", "type": "Frigate", "capacity": 80, "cannons": 15},
        headers={"X-API-KEY": "invalid-key"},
    )
    assert response.status_code == 401


def test_get_ships_pagination_and_sorting(client):
    client.post(
        "/ships",
        json={"name": "Black Pearl", "type": "Galleon", "capacity": 100, "cannons": 20},
        headers={"X-API-KEY": "test-api-key"},
    )
    client.post(
        "/ships",
        json={"name": "Flying Dutchman", "type": "Frigate", "capacity": 80, "cannons": 15},
        headers={"X-API-KEY": "test-api-key"},
    )
    response = client.get("/ships?skip=0&limit=1&sort_by=name&order=asc")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_ship_by_id(client):
    client.post(
        "/ships",
        json={"name": "Black Pearl", "type": "Galleon", "capacity": 100, "cannons": 20},
        headers={"X-API-KEY": "test-api-key"},
    )
    response = client.get("/ships/0")
    assert response.status_code == 200
    assert response.json()["name"] == "Black Pearl"


def test_create_treasure(client):
    response = client.post(
        "/treasures",
        json={"name": "Gold Chest", "value": 1000.0, "location": "Island", "is_cursed": False},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Gold Chest"


def test_create_extended_pirate(client):
    response = client.post(
        "/pirates/extended",
        json={
            "name": "Jack Sparrow",
            "age": 40,
            "ship": "Black Pearl",
            "rank": "captain",
            "skills": ["swordsmanship", "navigation"],
            "treasures": [{"name": "Gold Chest", "value": 1000.0}],
        },
        cookies={"session_id": "test-session"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Jack Sparrow"
