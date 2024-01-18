#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import click

from questionpy_sdk.commands._helper import infer_package_kind
from questionpy_sdk.webserver.app import WebServer


@click.command()
@click.argument("package")
def run(package: str) -> None:
    web_server = WebServer(infer_package_kind(package))
    web_server.start_server()
