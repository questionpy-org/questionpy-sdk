import logging
from pathlib import Path
from shutil import copytree
from typing import Optional

from questionpy_common.manifest import ensure_is_valid_name, DEFAULT_NAMESPACE

import click
import yaml

log = logging.getLogger(__name__)


# TODO: use partial model validation instead of accessing the validator directly.
#       This feature will be available in pydantic V2:
#       https://github.com/pydantic/pydantic/pull/3179#issuecomment-1205328414
def validate_short_name(context: click.Context, _parameter: click.Parameter, value: Path) -> Path:
    try:
        ensure_is_valid_name(value.name)
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
@click.argument("short_name", callback=validate_short_name, type=click.Path(exists=False, path_type=Path))
@click.option("--namespace", "-n", "namespace", callback=validate_namespace, default=DEFAULT_NAMESPACE)
def create(short_name: Path, namespace: str) -> None:
    template_path = Path("example")
    copytree(template_path, short_name)

    manifest_path = short_name.joinpath("qpy_manifest.yml")

    with manifest_path.open("r") as manifest_f:
        manifest = yaml.safe_load(manifest_f)

    manifest["short_name"] = short_name.name
    manifest["namespace"] = namespace

    with manifest_path.open("w") as manifest_f:
        yaml.dump(manifest, manifest_f, sort_keys=False)
