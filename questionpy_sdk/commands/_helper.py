#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import zipfile
from pathlib import Path

import click
from pydantic import ValidationError

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_sdk.package.builder import DirPackageBuilder
from questionpy_sdk.package.errors import PackageBuildError, PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource
from questionpy_server.worker.runtime.package_location import (
    DirPackageLocation,
    PackageLocation,
    ZipPackageLocation,
)


def _get_dir_package_location(source_path: Path) -> DirPackageLocation:
    try:
        return DirPackageLocation(source_path)
    except (OSError, ValidationError, ValueError) as exc:
        msg = f"Failed to read package manifest:\n{exc}"
        raise click.ClickException(msg) from exc


def _get_dir_package_location_from_source(pkg_string: str, source_path: Path) -> DirPackageLocation:
    # Always rebuild package.
    try:
        package_source = PackageSource(source_path)
    except PackageSourceValidationError as exc:
        raise click.ClickException(str(exc)) from exc
    try:
        with DirPackageBuilder(package_source) as builder:
            builder.write_package()
            click.echo(f"Successfully built package '{pkg_string}'.")
    except PackageBuildError as exc:
        msg = f"Failed to build package: {exc}"
        raise click.ClickException(msg) from exc

    return _get_dir_package_location(source_path / DIST_DIR)


def get_package_location(pkg_string: str, pkg_path: Path) -> PackageLocation:
    if pkg_path.is_dir():
        # dist dir
        if (pkg_path / MANIFEST_FILENAME).is_file():
            return _get_dir_package_location(pkg_path)
        # source dir
        return _get_dir_package_location_from_source(pkg_string, pkg_path)

    if zipfile.is_zipfile(pkg_path):
        return ZipPackageLocation(pkg_path)

    msg = f"'{pkg_string}' doesn't look like a QPy package file, source directory, or dist directory."
    raise click.ClickException(msg)


def confirm_overwrite(filepath: Path) -> bool:
    return click.confirm(f"The path '{filepath}' already exists. Do you want to overwrite it?", abort=True)
