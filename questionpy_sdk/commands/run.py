import logging
import sys
from importlib import import_module
from pathlib import Path

import click

from questionpy import QuestionType
from questionpy_sdk.package import QPyPackage
from questionpy_sdk.runtime import run_qtype
from questionpy_sdk.server import QPyPackageServer

log = logging.getLogger(__name__)


@click.command()
@click.argument("package", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-p", "--pretty", is_flag=True, show_default=True, default=False, help="Output indented JSON.")
def run(package: Path, pretty: bool) -> None:
    with QPyPackage(package, "r") as package_file:
        old_path = sys.path
        sys.path = [str(package / "python"), str(package / "dependencies/site-packages"), *sys.path]

        log.debug("Modified sys.path is '%s'", sys.path)
        try:
            import_module(package_file.manifest.entrypoint)

            if QuestionType.implementation is None:
                log.fatal("The package '%s' does not contain an implementation of QuestionType", package)
                sys.exit(1)

            server = QPyPackageServer(sys.stdin, sys.stdout, pretty=pretty)
            run_qtype(package_file.manifest, QuestionType.implementation, server)
        finally:
            sys.path = old_path
            log.debug("Reset sys.path to '%s'", sys.path)
