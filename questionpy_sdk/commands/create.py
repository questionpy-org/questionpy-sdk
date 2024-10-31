#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import click

from cookiecutter.exceptions import CookiecutterException
from cookiecutter.main import cookiecutter
from questionpy_common.manifest import DEFAULT_NAMESPACE

COOKIECUTTER_PATH = str((Path(__file__).parent.parent.parent / "cookiecutter").resolve())


@click.command(context_settings={"show_default": True})
@click.option("--short-name", "-s", "short_name", default="my_questionpy_package", help="Package short name.")
@click.option("--namespace", "-n", "namespace", default=DEFAULT_NAMESPACE, help="Package namespace.")
@click.option(
    "--out",
    "-o",
    "out_path",
    type=click.Path(path_type=Path),
    help="Newly created package directory.  [default: short-name]",
)
def create(short_name: str, namespace: str, out_path: Path | None) -> None:
    """Create new package."""
    if not out_path:
        out_path = Path(short_name)

    try:
        extra_context = {"short_name": short_name, "namespace": namespace}
        cookiecutter(COOKIECUTTER_PATH, extra_context=extra_context, output_dir=out_path)
    except CookiecutterException as err:
        raise click.ClickException(err) from err
