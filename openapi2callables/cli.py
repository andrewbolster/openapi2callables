"""Console script for openapi2callables."""

import click

from .parse import get_spec, parse_spec
from .server import app


@click.group()
def cli(): ...


@cli.command()
@click.argument("schema_url")
def parse(schema_url):
    """Parse an OpenAPI schema from a remote URL."""
    spec = get_spec(schema_url)
    tools = parse_spec(spec)
    click.echo(tools)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to listen on")
@click.option("--port", default=8000, help="Port to listen on")
def test_service(host="0.0.0.0", port=8000):
    """Host a small test service to test against. Useful for development, not sure who else."""
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    cli()
