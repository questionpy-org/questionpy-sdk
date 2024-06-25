#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import click

from questionpy_sdk.commands._helper import get_package_location
from questionpy_sdk.webserver.app import WebServer


@click.command()
@click.argument("package")
def run(package: str) -> None:
    """Run a package.

    \b
    PACKAGE can be:
    - a .qpy file,
    - a dist directory, or
    - a source directory (built on-the-fly).
    """  # noqa: D301
    web_server = WebServer(get_package_location(package))
    web_server.start_server()
