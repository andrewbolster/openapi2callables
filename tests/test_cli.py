from unittest.mock import patch

import pytest
import requests
from click.testing import CliRunner

from openapi2callables.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_help_command(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output


@patch("openapi2callables.cli.get_spec")
@patch("openapi2callables.cli.parse_spec")
def test_parse_command_valid(mock_parse_spec, mock_get_spec, runner):
    mock_get_spec.return_value = {"openapi": "3.0.0"}
    mock_parse_spec.return_value = {"tool1": {"description": "Test tool"}}
    result = runner.invoke(cli, ["parse", "http://example.com/openapi.json"])
    assert result.exit_code == 0
    assert "tool1" in result.output


@patch("openapi2callables.cli.get_spec", side_effect=requests.exceptions.RequestException("Invalid URL"))
def test_parse_command_invalid(mock_get_spec, runner):
    result = runner.invoke(cli, ["parse", "http://invalid"])
    assert result.exit_code != 0
    assert "Could not fetch spec from URL" in result.output


def test_parse_command_missing_argument(runner):
    result = runner.invoke(cli, ["parse"])
    assert result.exit_code != 0
    assert "Error: Missing argument 'SCHEMA_URL'" in result.output
