#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
import shutil
import sys

import click

from questionpy_sdk.commands.create import create
from questionpy_sdk.commands.package import package
from questionpy_sdk.commands.repo import repo
from questionpy_sdk.commands.run import run

# Contrary to click's docs, there's no autodetection of the terminal width (pallets/click#2253)
terminal_width = shutil.get_terminal_size()[0]


@click.group(context_settings={"help_option_names": ["-h", "--help"], "terminal_width": terminal_width})
@click.option(
    "-n",
    "--no-interaction",
    is_flag=True,
    show_default=True,
    default=False,
    help="Do not ask any interactive question.",
)
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Use log level DEBUG.")
@click.pass_context
def cli(ctx: click.Context, *, verbose: bool, no_interaction: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, stream=sys.stderr)
    ctx.ensure_object(dict)
    ctx.obj["no_interaction"] = no_interaction


cli.add_command(create)
cli.add_command(package)
cli.add_command(run)
cli.add_command(repo)

if __name__ == "__main__":
    cli()
