#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import click
import yaml
from questionpy_common.manifest import ensure_is_valid_name, DEFAULT_NAMESPACE

from questionpy_sdk.resources import EXAMPLE_PACKAGE

log = logging.getLogger(__name__)


def validate_name(context: click.Context, _parameter: click.Parameter, value: str) -> str:
    # We could model_validate() the manifest dict instead, but the pydantic.ValidationError would lead to a less nice
    # error message. If we end up doing this in lots of places, converting the ValidationError to a custom
    # click.UsageError might be nice.
    try:
        return ensure_is_valid_name(value)
    except ValueError as error:
        raise click.BadParameter(str(error), ctx=context) from error


@click.command(context_settings={"show_default": True})
@click.argument("short_name", callback=validate_name)
@click.option("--namespace", "-n", "namespace", callback=validate_name, default=DEFAULT_NAMESPACE)
@click.option("--out", "-o", "out_path", type=click.Path(path_type=Path))
def create(short_name: str, namespace: str, out_path: Optional[Path]) -> None:
    if not out_path:
        out_path = Path(short_name)
    if out_path.exists():
        raise click.ClickException(f"The path '{out_path}' already exists.")

    with ZipFile(EXAMPLE_PACKAGE) as zip_file:
        zip_file.extractall(out_path)

    # Rename namespaced python folder.
    python_folder = out_path / "python"
    namespace_folder = (python_folder / "local").rename(python_folder / namespace)
    (namespace_folder / "example").rename(namespace_folder / short_name)

    manifest_path = out_path / "qpy_manifest.yml"

    with manifest_path.open("r") as manifest_f:
        manifest = yaml.safe_load(manifest_f)

    manifest["short_name"] = short_name
    manifest["namespace"] = namespace

    with manifest_path.open("w") as manifest_f:
        yaml.dump(manifest, manifest_f, sort_keys=False)
