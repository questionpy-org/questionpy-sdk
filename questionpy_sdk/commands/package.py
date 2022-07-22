import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import click

from questionpy import Manifest
from questionpy_sdk.package import QPyPackage

log = logging.getLogger(__name__)


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--manifest", "-m", "manifest_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def package(source: Path, manifest_path: Optional[Path]) -> None:
    out_path = source.with_suffix(".qpy")

    if not manifest_path:
        manifest_path = source / "qpy_manifest.yml"

    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)

    manifest = Manifest.parse_file(manifest_path)

    with QPyPackage(out_path, "w") as out_file:
        install_dependencies(out_file, manifest_path, manifest)
        out_file.write_glob("python", source, "**/*.py")
        out_file.write_manifest(manifest)


def install_dependencies(target: QPyPackage, manifest_path: Path, manifest: Manifest) -> None:
    if isinstance(manifest.requirements, str):
        # treat as a relative reference to a requirements.txt and read those
        pip_args = ["-r", str(manifest_path.parent / manifest.requirements)]
    elif isinstance(manifest.requirements, list):
        # treat as individual dependency specifiers
        pip_args = manifest.requirements
    else:
        # no dependencies specified
        return

    with TemporaryDirectory(prefix=f"qpy_{manifest.short_name}") as tempdir:
        subprocess.run(["pip", "install", "--target", tempdir, *pip_args], check=True)
        target.write_glob("dependencies/site-packages", Path(tempdir), "**/*")
