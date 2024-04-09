#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import importlib.util
import zipfile
from pathlib import Path

import click

from questionpy_sdk.package.errors import PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource
from questionpy_server.worker.runtime.package_location import (
    DirPackageLocation,
    FunctionPackageLocation,
    PackageLocation,
    ZipPackageLocation,
)


def read_package_source(source_path: Path) -> PackageSource:
    try:
        return PackageSource(source_path)
    except PackageSourceValidationError as exc:
        raise click.ClickException(str(exc)) from exc


def infer_package_kind(string: str) -> PackageLocation:
    path = Path(string)
    if path.is_dir():
        package_source = read_package_source(path)
        return DirPackageLocation(path, package_source.config)

    if zipfile.is_zipfile(path):
        return ZipPackageLocation(path)

    if ":" in string:
        # Explicitly provided init function name.
        module_name, function_name = string.rsplit(":", maxsplit=1)
    else:
        # Default init function name.
        module_name, function_name = string, "init"

    # https://stackoverflow.com/a/14050282/5390250
    try:
        module_spec = importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        # find_spec returns None when the leaf package isn't found, but it raises if any of the parent packages aren't.
        module_spec = None

    if module_spec:
        return FunctionPackageLocation(module_name, function_name)

    msg = f"'{string}' doesn't look like a QPy package zip file, directory or module"
    raise click.ClickException(msg)


def confirm_overwrite(filepath: Path) -> bool:
    return click.confirm(f"The path '{filepath}' already exists. Do you want to overwrite it?", abort=True)
