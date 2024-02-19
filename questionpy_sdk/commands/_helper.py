#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import importlib.util
import zipfile
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from questionpy_common.manifest import Manifest
from questionpy_server.worker.runtime.package_location import PackageLocation, DirPackageLocation, ZipPackageLocation, \
    FunctionPackageLocation
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.models import PackageConfig


def create_normalized_filename(manifest: Manifest) -> str:
    """
    Creates a normalized file name for the given manifest.

    Args:
        manifest: manifest of the package

    Returns:
        normalized file name
    """
    return f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.qpy"


def infer_package_kind(string: str) -> PackageLocation:
    path = Path(string)
    if path.is_dir():
        config = read_yaml_config(path / PACKAGE_CONFIG_FILENAME)
        return DirPackageLocation(path, config)

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

    raise click.ClickException(f"'{string}' doesn't look like a QPy package zip file, directory or module")


def read_yaml_config(path: Path) -> PackageConfig:
    if not path.is_file():
        raise click.ClickException(f"The config '{path}' does not exist.")

    with path.open() as config_f:
        try:
            return PackageConfig.model_validate(yaml.safe_load(config_f))
        except yaml.YAMLError as e:
            raise click.ClickException(f"Failed to parse config '{path}': {e}")
        except ValidationError as e:
            raise click.ClickException(f"Invalid config '{path}': {e}")
