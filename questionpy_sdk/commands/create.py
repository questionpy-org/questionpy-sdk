#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from zipfile import ZipFile

import click
import yaml

from questionpy_common.manifest import DEFAULT_NAMESPACE, ensure_is_valid_name
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.resources import EXAMPLE_PACKAGE


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
def create(short_name: str, namespace: str, out_path: Path | None) -> None:
    if not out_path:
        out_path = Path(short_name)
    if out_path.exists():
        msg = f"The path '{out_path}' already exists."
        raise click.ClickException(msg)

    with ZipFile(EXAMPLE_PACKAGE) as zip_file:
        zip_file.extractall(out_path)

    # Rename namespaced python folder.
    python_folder = out_path / "python"
    namespace_folder = (python_folder / "local").rename(python_folder / namespace)
    (namespace_folder / "minimal_example").rename(namespace_folder / short_name)

    config_path = out_path / PACKAGE_CONFIG_FILENAME

    with config_path.open("r") as config_f:
        config = yaml.safe_load(config_f)

    config["short_name"] = short_name
    config["namespace"] = namespace

    with config_path.open("w") as config_f:
        yaml.dump(config, config_f, sort_keys=False)
