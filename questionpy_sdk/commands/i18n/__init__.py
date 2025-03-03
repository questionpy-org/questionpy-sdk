import click

from questionpy_sdk.commands.i18n._extract import extract
from questionpy_sdk.commands.i18n._init import init
from questionpy_sdk.commands.i18n._update import update


@click.group()
def i18n() -> None:
    """Manage translations for a package."""


i18n.add_command(extract)
i18n.add_command(init)
i18n.add_command(update)
