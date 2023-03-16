import click

from questionpy_sdk.commands.repo.structure import structure
from questionpy_sdk.commands.repo.index import index


@click.group()
def repo() -> None:
    """Repository commands."""


repo.add_command(structure)
repo.add_command(index)
