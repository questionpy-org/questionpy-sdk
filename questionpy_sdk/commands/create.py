import logging
from pathlib import Path
from shutil import copytree, ignore_patterns
from importlib.resources import files, as_file
from typing import Optional

from questionpy_common.manifest import ensure_is_valid_name, DEFAULT_NAMESPACE

import click
import yaml
import example

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
        raise click.ClickException(f"The path '{out_path}' already exists.")

    template = files(example)

    with as_file(template) as template_path:
        copytree(template_path, out_path, ignore=ignore_patterns("__pycache__"))

    # Rename namespaced python folder.
    python_folder = out_path / "python"
    namespace_folder = (python_folder / "local").rename(python_folder / namespace)
    (namespace_folder / "example").rename(namespace_folder / short_name)

    # Remove __init__.py from package as we only need it here to do `import example`.
    (out_path / "__init__.py").unlink()

    manifest_path = out_path.joinpath("qpy_manifest.yml")

    with manifest_path.open("r") as manifest_f:
        manifest = yaml.safe_load(manifest_f)

    manifest["short_name"] = short_name
    manifest["namespace"] = namespace

    with manifest_path.open("w") as manifest_f:
        yaml.dump(manifest, manifest_f, sort_keys=False)
