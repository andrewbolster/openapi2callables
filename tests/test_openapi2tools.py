#!/usr/bin/env python
"""Tests for `openapi2tools` package."""

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from openapi2tools import cli, server


@pytest.fixture
def client():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    client = TestClient(server.app)
    return client


def test_content(client):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    response = client.get("/pirate")
    assert response.status_code == 200
    assert response.json() == "Arr, matey! Welcome to the pirate endpoint!"


def test_openapi_endpoint(client):
    """Test the OpenAPI endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == server.app.openapi()


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert "openapi2tools" in result.output
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "--help  Show this message and exit." in help_result.output
