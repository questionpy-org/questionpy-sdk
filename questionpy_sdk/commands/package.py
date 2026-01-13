#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import Sequence
from pathlib import Path

import click

from questionpy_common.constants import DIST_DIR
from questionpy_sdk._dependency_resolver import SdkDynamicDependencyResolver
from questionpy_sdk._package import ZipBuildTarget, build_qpy_package
from questionpy_sdk._package.errors import PackageBuildError, PackageSourceValidationError
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.commands._helper import confirm_overwrite
from questionpy_server.dependencies import DynamicDependencyResolver


def validate_out_path(context: click.Context, _parameter: click.Parameter, value: Path | None) -> Path | None:
    if value and not value.is_dir() and value.suffix != ".qpy":
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
    help="Output directory or file path of QuestionPy package. [default: 'NAMESPACE-SHORT_NAME-VERSION.qpy']",
)
@click.option(
    "--without-sources",
    "without_sources",
    is_flag=True,
    help="Don't copy package sources into the .qpy file.",
)
@click.option("--force", "-f", "allow_overwrite", is_flag=True, help="Force overwriting of output file.")
@click.option(
    "--local-deps-from",
    "-L",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to a local directory to search for dependencies in.",
    multiple=True,
)
@click.pass_context
def package(
    ctx: click.Context,
    source: Path,
    out_path: Path | None,
    local_deps_from: Sequence[Path],
    *,
    allow_overwrite: bool,
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
        ("--force", allow_overwrite),
    ):
        if param and development:
            msg = f"The options {param_name} and --dev are mutually exclusive."
            raise click.UsageError(msg, ctx=ctx)

    dependency_resolver = SdkDynamicDependencyResolver(local_deps_from)

    if development:
        create_dist(package_source, dependency_resolver=dependency_resolver)

    else:
        if not out_path:
            # Use default filename in current working directory.
            out_path = Path(package_source.normalized_filename)
        elif out_path.is_dir():
            # Use default filename inside the given directory.
            out_path /= package_source.normalized_filename

        create_qpy_package(
            ctx,
            package_source,
            out_path,
            allow_overwrite=allow_overwrite,
            without_sources=without_sources,
            dependency_resolver=dependency_resolver,
        )


def create_dist(package_source: PackageSource, *, dependency_resolver: DynamicDependencyResolver) -> None:
    try:
        build_qpy_package(package_source, dependency_resolver=dependency_resolver)
    except PackageBuildError as exc:
        msg = f"Failed to build package: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(f"Successfully created '{package_source.path / DIST_DIR}'.")


def create_qpy_package(
    ctx: click.Context,
    package_source: PackageSource,
    out_path: Path,
    *,
    allow_overwrite: bool,
    without_sources: bool,
    dependency_resolver: DynamicDependencyResolver,
) -> None:
    if out_path.exists() and not allow_overwrite:
        if not ctx.obj["no_interaction"]:
            allow_overwrite = confirm_overwrite(out_path)
        else:
            msg = f"Output file '{out_path}' exists"
            raise click.ClickException(msg)

    try:
        build_qpy_package(
            package_source,
            ZipBuildTarget(out_path, allow_overwrite=allow_overwrite),
            copy_sources=not without_sources,
            dependency_resolver=dependency_resolver,
        )
    except PackageBuildError as exc:
        msg = f"Failed to build package: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(f"Successfully created '{out_path}'.")
