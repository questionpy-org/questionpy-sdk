#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import shutil
import tempfile
from contextlib import suppress
from pathlib import Path

import click

from questionpy_common.constants import DIST_DIR
from questionpy_sdk.package.builder import DirPackageBuilder, ZipPackageBuilder
from questionpy_sdk.package.errors import PackageBuildError, PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource

from ._helper import confirm_overwrite


def validate_out_path(context: click.Context, _parameter: click.Parameter, value: Path | None) -> Path | None:
    if value and value.suffix != ".qpy":
        msg = "Packages need the extension '.qpy'."
        raise click.BadParameter(msg, ctx=context)
    return value


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--dev",
    "-d",
    "development",
    is_flag=True,
    help="Output to the 'dist' folder within the source directory, rather than generating a .qpy file.",
)
@click.option(
    "--out",
    "-o",
    "out_path",
    callback=validate_out_path,
    type=click.Path(path_type=Path),
    help="Output file path of QuestionPy package. [default: 'NAMESPACE-SHORT_NAME-VERSION.qpy']",
)
@click.option(
    "--without-sources",
    "without_sources",
    is_flag=True,
    help="Don't copy package sources into the .qpy file.",
)
@click.option("--force", "-f", "force_overwrite", is_flag=True, help="Force overwriting of output file.")
@click.pass_context
def package(
    ctx: click.Context,
    source: Path,
    out_path: Path | None,
    *,
    force_overwrite: bool,
    development: bool,
    without_sources: bool,
) -> None:
    """Build package from directory SOURCE."""
    try:
        package_source = PackageSource(source)
    except PackageSourceValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    for param_name, param in (
        ("--out", out_path),
        ("--without-sources", without_sources),
        ("--force", force_overwrite),
    ):
        if param and development:
            msg = f"The options {param_name} and --dev are mutually exclusive."
            raise click.UsageError(msg, ctx=ctx)

    if development:
        create_dist(ctx, package_source)

    else:
        if not out_path:
            out_path = Path(package_source.normalized_filename)
        create_qpy_package(
            ctx, package_source, out_path, force_overwrite=force_overwrite, without_sources=without_sources
        )


def create_dist(ctx: click.Context, package_source: PackageSource) -> None:
    try:
        with DirPackageBuilder(package_source) as builder:
            builder.write_package()
    except PackageBuildError as exc:
        msg = f"Failed to build package: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(f"Successfully created '{package_source.path / DIST_DIR}'.")


def create_qpy_package(
    ctx: click.Context, package_source: PackageSource, out_path: Path, *, force_overwrite: bool, without_sources: bool
) -> None:
    overwriting = False

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
            with ZipPackageBuilder(temp_file, package_source, copy_sources=not without_sources) as builder:
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
