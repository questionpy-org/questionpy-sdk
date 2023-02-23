import logging
from importlib.resources import files, as_file
from pathlib import Path
from shutil import rmtree
from typing import Optional
from zipfile import ZipFile

import click
import yaml

from questionpy_common.manifest import ensure_is_valid_name, DEFAULT_NAMESPACE

from questionpy_sdk import resources


log = logging.getLogger(__name__)


# TODO: use partial model validation instead of accessing the validator directly.
#       This feature will be available in pydantic V2:
#       https://github.com/pydantic/pydantic/pull/3179#issuecomment-1205328414
def validate_short_name(context: click.Context, _parameter: click.Parameter, value: str) -> str:
    try:
        ensure_is_valid_name(value)
    except ValueError as error:
        raise click.BadParameter(str(error), ctx=context) from error
    return value


def validate_namespace(context: click.Context, _parameter: click.Parameter, value: Optional[str]) -> Optional[str]:
    try:
        if value is not None:
            ensure_is_valid_name(value)
    except ValueError as error:
        raise click.BadParameter(str(error), ctx=context) from error
    return value


@click.command(context_settings={"show_default": True})
@click.argument("short_name", callback=validate_short_name)
@click.option("--namespace", "-n", "namespace", callback=validate_namespace, default=DEFAULT_NAMESPACE)
@click.option("--out", "-o", "out_path", type=click.Path(path_type=Path))
def create(short_name: str, namespace: str, out_path: Optional[Path]) -> None:
    if not out_path:
        out_path = Path(short_name)
    if out_path.exists():
        if not click.confirm(f"The path '{out_path}' already exists. Do you want to override it?"):
            return
        rmtree(out_path)

    template = files(resources) / "example.zip"
    with as_file(template) as template_path:
        ZipFile(template_path).extractall(out_path)

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
