"""Console script for openapi2callables."""
import click

from .parse import get_spec
from .parse import parse_spec
from .server import app


@click.group()
def cli():
    ...


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to listen on")
@click.option("--port", default=8000, help="Port to listen on")
def serve(host="0.0.0.0", port=8000):
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


@cli.command()
@click.argument("schema_url")
def parse(schema_url):
    spec = get_spec(schema_url)
    tools = parse_spec(spec)
    click.echo(tools)


if __name__ == "__main__":
    cli()
