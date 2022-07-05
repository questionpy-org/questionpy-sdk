import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from zipfile import ZipFile

import click as click

from questionpy.sdk.manifest import Manifest

log = logging.getLogger(__name__)

package: click.Command


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--manifest", "-m", "manifest_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def package(source: Path, manifest_path: Optional[Path]):
    out_path = source.with_suffix(".qpy")

    if not manifest_path:
        manifest_path = source / "qpy_manifest.yml"

    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)

    manifest = Manifest.parse_file(manifest_path)

    with ZipFile(out_path.open("wb"), "w") as out_file:
        install_dependencies(out_file, manifest_path, manifest)

        for source_file in source.glob("**/*.py"):
            path_in_pkg = source_file.relative_to(source)
            log.info(f"{path_in_pkg}: {source_file}")
            out_file.write(source_file, path_in_pkg)

        log.info(f"qpy_manifest.yml: {manifest}")
        out_file.writestr("qpy_manifest.yml", manifest.yaml())


def install_dependencies(target: ZipFile, manifest_path: Path, manifest: Manifest):
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

        for file in Path(tempdir).glob("**/*"):
            path_in_pkg = file.relative_to(tempdir)
            log.info(f"{path_in_pkg}: {file}")
            target.write(file, path_in_pkg)
