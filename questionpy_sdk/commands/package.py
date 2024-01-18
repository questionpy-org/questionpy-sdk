#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import inspect
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Optional

import click
from questionpy_common.manifest import Manifest

import questionpy
from questionpy_sdk.commands._helper import create_normalized_filename, read_yaml_manifest
from questionpy_sdk.package import PackageBuilder


def validate_out_path(context: click.Context, _parameter: click.Parameter, value: Optional[Path]) -> Optional[Path]:
    if value and value.suffix != '.qpy':
        raise click.BadParameter("Packages need the extension '.qpy'.", ctx=context)
    return value


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--manifest", "-m", "manifest_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "-o", "out_path", callback=validate_out_path, type=click.Path(path_type=Path))
def package(source: Path, manifest_path: Optional[Path], out_path: Optional[Path]) -> None:
    if not manifest_path:
        manifest_path = source / "qpy_manifest.yml"

    manifest = read_yaml_manifest(manifest_path)

    if not out_path:
        out_path = Path(create_normalized_filename(manifest))
    if out_path.exists():
        if click.confirm(f"The path '{out_path}' already exists. Do you want to overwrite it?", abort=True):
            out_path.unlink()

    try:
        with PackageBuilder(out_path) as out_file:
            _copy_package(out_file, questionpy)
            _install_dependencies(out_file, manifest_path, manifest)
            out_file.write_glob(source, "python/**/*")
            out_file.write_glob(source, "static/**/*")
            out_file.write_manifest(manifest)
    except subprocess.CalledProcessError as e:
        out_path.unlink(missing_ok=True)
        raise click.ClickException(f"Failed to install requirements: {e.stderr.decode()}")

    click.echo(f"Successfully created '{out_path}'.")


def _install_dependencies(target: PackageBuilder, manifest_path: Path, manifest: Manifest) -> None:
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
        subprocess.run(["pip", "install", "--target", tempdir, *pip_args], check=True, capture_output=True)
        target.write_glob(Path(tempdir), "**/*", prefix="dependencies/site-packages")


def _copy_package(target: PackageBuilder, pkg: ModuleType) -> None:
    # inspect.getfile returns the path to the package's __init__.py
    package_dir = Path(inspect.getfile(pkg)).parent
    target.write_glob(package_dir, "**/*.py", prefix=f"dependencies/site-packages/{pkg.__name__}")
