import click as click

from questionpy.sdk.commands.package import package
from questionpy.sdk.commands.run import run
from questionpy.sdk.logging import init_logging


@click.group()
def cli():
    init_logging()


cli.add_command(package)
cli.add_command(run)

if __name__ == '__main__':
    cli()
