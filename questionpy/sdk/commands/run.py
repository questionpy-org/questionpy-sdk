import sys
from importlib import import_module
from pathlib import Path
from zipfile import ZipFile

import click

from questionpy.sdk.manifest import Manifest
from questionpy.sdk.qtype import QuestionType
from questionpy.sdk.runtime import QPyRuntime

run: click.Command


@click.command()
@click.argument("package", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-p", "--pretty", is_flag=True, show_default=True, default=False, help="Output indented JSON.")
def run(package: Path, pretty: bool):
    with ZipFile(package) as package_file:
        manifest = Manifest.parse_raw(package_file.read("qpy_manifest.yml"))

    sys.path.insert(0, str(package))
    try:
        import_module(manifest.entrypoint)
    finally:
        sys.path.remove(str(package))

    runtime = QPyRuntime(manifest, QuestionType.__subclasses__()[0], pretty=pretty)
    runtime.run()
