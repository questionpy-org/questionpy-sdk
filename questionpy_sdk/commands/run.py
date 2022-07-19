import logging
import sys
from importlib import import_module
from pathlib import Path
from zipfile import ZipFile

import click

from questionpy import Manifest, QuestionType
from questionpy_sdk.runtime import run_qtype
from questionpy_sdk.server import QPyPackageServer

log = logging.getLogger(__name__)


@click.command()
@click.argument("package", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-p", "--pretty", is_flag=True, show_default=True, default=False, help="Output indented JSON.")
def run(package: Path, pretty: bool) -> None:
    with ZipFile(package) as package_file:
        manifest = Manifest.parse_raw(package_file.read("qpy_manifest.yml"))

    sys.path.insert(0, str(package))
    try:
        import_module(manifest.entrypoint)
    finally:
        sys.path.remove(str(package))

    if QuestionType.implementation is None:
        log.fatal("The package '%s' does not contain an implementation of QuestionType", package)
        sys.exit(1)

    server = QPyPackageServer(sys.stdin, sys.stdout, pretty=pretty)
    run_qtype(manifest, QuestionType.implementation, server)
