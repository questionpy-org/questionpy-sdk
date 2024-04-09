#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import shutil
import tempfile
from contextlib import suppress
from pathlib import Path

import click

from questionpy_sdk.package.builder import PackageBuilder
from questionpy_sdk.package.errors import PackageBuildError

from ._helper import confirm_overwrite, read_package_source


def validate_out_path(context: click.Context, _parameter: click.Parameter, value: Path | None) -> Path | None:
    if value and value.suffix != ".qpy":
        msg = "Packages need the extension '.qpy'."
        raise click.BadParameter(msg, ctx=context)
    return value


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--out",
    "-o",
    "out_path",
    callback=validate_out_path,
    type=click.Path(path_type=Path),
    help="Output file path of QuestionPy package. [default: 'NAMESPACE-SHORT_NAME-VERSION.qpy']",
)
@click.option("--force", "-f", "force_overwrite", is_flag=True, help="Force overwriting of output file.")
@click.pass_context
def package(ctx: click.Context, source: Path, out_path: Path | None, *, force_overwrite: bool) -> None:
    """Build package from directory SOURCE."""
    package_source = read_package_source(source)
    overwriting = False

    if not out_path:
        out_path = Path(package_source.normalized_filename)

    if out_path.exists():
        if force_overwrite or (not ctx.obj["no_interaction"] and confirm_overwrite(out_path)):
            overwriting = True
        else:
            msg = f"Output file '{out_path}' exists"
            raise click.ClickException(msg)

    try:
        # Use temp file, otherwise we risk overwriting `out_path` in case of a build error.
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_path = Path(temp_file.name)

        try:
            with PackageBuilder(temp_file, package_source) as builder:
                builder.write_package()
        except PackageBuildError as exc:
            msg = f"Failed to build package: {exc}"
            raise click.ClickException(msg) from exc
        finally:
            temp_file.close()

        if overwriting:
            Path(out_path).unlink()

        shutil.move(temp_file_path, out_path)
    finally:
        with suppress(FileNotFoundError):
            temp_file_path.unlink()

    click.echo(f"Successfully created '{out_path}'.")
