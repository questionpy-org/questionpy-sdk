#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
import sys

import click

from questionpy_sdk.commands.create import create
from questionpy_sdk.commands.package import package
from questionpy_sdk.commands.run import run

from questionpy_sdk.commands.repo import repo


@click.group(context_settings={"help_option_names": ['-h', '--help']})
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Use log level DEBUG.")
def cli(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)


cli.add_command(create)
cli.add_command(package)
cli.add_command(run)
cli.add_command(repo)

if __name__ == '__main__':
    # PyLint doesn't understand that click.group doesn't return a function
    # pylint: disable=no-value-for-parameter
    cli()
