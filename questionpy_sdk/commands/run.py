#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from pathlib import Path

import click

from questionpy_sdk.webserver.app import WebServer

log = logging.getLogger(__name__)


@click.command()
@click.argument("package", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def run(package: Path) -> None:
    web_server = WebServer(package)
    web_server.start_server()
