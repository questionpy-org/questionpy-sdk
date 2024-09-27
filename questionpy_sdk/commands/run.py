#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from pathlib import Path

import click

from questionpy_sdk.commands._helper import get_package_location
from questionpy_sdk.webserver.app import DEFAULT_STATE_STORAGE_PATH, WebServer


@click.command()
@click.argument("package")
@click.option(
    "--state-storage-path",
    type=click.Path(path_type=Path, exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_STATE_STORAGE_PATH,
    envvar="QPY_STATE_STORAGE_PATH",
)
def run(package: str, state_storage_path: Path) -> None:
    """Run a package.

    \b
    PACKAGE can be:
    - a .qpy file,
    - a dist directory, or
    - a source directory (built on-the-fly).
    """  # noqa: D301
    pkg_path = Path(package).resolve()
    web_server = WebServer(get_package_location(package, pkg_path), state_storage_path)
    web_server.start_server()
