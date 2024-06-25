"""Console script for openapi2tools."""

import click


@click.command()
def main():
    """Main entrypoint."""
    click.echo("openapi2tools")
    click.echo("=" * len("openapi2tools"))
    click.echo(
        "Experiment in parsing and projecting OpenAPI endpoints into OpenAI/GenericLLM compatible Tools "
        "(but should also be generic enough for non-llm directed usage...)"
    )


if __name__ == "__main__":
    main()  # pragma: no cover
