#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import zipfile
from pathlib import Path

import click
from pydantic import ValidationError

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_common.manifest import Manifest
from questionpy_sdk.package.builder import DirPackageBuilder
from questionpy_sdk.package.errors import PackageBuildError, PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource
from questionpy_server.worker.runtime.package_location import (
    DirPackageLocation,
    PackageLocation,
    ZipPackageLocation,
)


def build_dir_package(source_path: Path) -> None:
    try:
        package_source = PackageSource(source_path)
    except PackageSourceValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        with DirPackageBuilder(package_source) as builder:
            builder.write_package()
    except PackageBuildError as exc:
        msg = f"Failed to build package: {exc}"
        raise click.ClickException(msg) from exc


def get_package_location(pkg_string: str) -> PackageLocation:
    pkg_path = Path(pkg_string)

    if pkg_path.is_dir():
        # Always rebuild package.
        build_dir_package(pkg_path)
        click.echo(f"Successfully built package '{pkg_string}'.")
        try:
            manifest_path = pkg_path / DIST_DIR / MANIFEST_FILENAME
            with manifest_path.open() as manifest_fp:
                manifest = Manifest.model_validate_json(manifest_fp.read())
            return DirPackageLocation(pkg_path, manifest)
        except (OSError, ValidationError, ValueError) as exc:
            msg = f"Failed to read package manifest:\n{exc}"
            raise click.ClickException(msg) from exc

    if zipfile.is_zipfile(pkg_path):
        return ZipPackageLocation(pkg_path)

    msg = f"'{pkg_string}' doesn't look like a QPy package zip file or directory."
    raise click.ClickException(msg)


def confirm_overwrite(filepath: Path) -> bool:
    return click.confirm(f"The path '{filepath}' already exists. Do you want to overwrite it?", abort=True)
