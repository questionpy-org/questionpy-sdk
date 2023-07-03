#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import click

from questionpy_sdk.commands.repo.structure import structure
from questionpy_sdk.commands.repo.index import index


@click.group()
def repo() -> None:
    """Repository commands."""


repo.add_command(structure)
repo.add_command(index)
