import pytest
from click.testing import CliRunner

from openapi2callables.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_help_command(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
