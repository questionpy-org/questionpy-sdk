import click

from questionpy_sdk.commands.package import package
from questionpy_sdk.commands.run import run
from questionpy_sdk.logging import init_logging


@click.group()
def cli() -> None:
    init_logging()


cli.add_command(package)
cli.add_command(run)

if __name__ == '__main__':
    cli()
