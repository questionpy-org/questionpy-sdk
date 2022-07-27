import logging
import sys

import click

from questionpy_sdk.commands.package import package
from questionpy_sdk.commands.run import run


@click.group()
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Use log level DEBUG.")
def cli(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)


cli.add_command(package)
cli.add_command(run)

if __name__ == '__main__':
    # PyLint doesn't understand that click.group doesn't return a function
    # pylint: disable=no-value-for-parameter
    cli()
