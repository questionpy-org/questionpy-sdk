from collections.abc import Collection
from pathlib import Path

import babel.messages.extract
import babel.messages.frontend
import babel.messages.pofile
import click
from click import ClickException

from questionpy.i18n import domain_of
from questionpy_common.manifest import Bcp47LanguageTag
from questionpy_sdk._i18n_utils import bcp47_to_posix
from questionpy_sdk.commands.i18n import extract
from questionpy_sdk.package.source import PackageSource


def _init_explicit(ctx: click.Context, pot: Path, localedir: Path, locale: Bcp47LanguageTag, *, force: bool) -> None:
    init_cmd = babel.messages.frontend.InitCatalog()
    init_cmd.locale = bcp47_to_posix(locale)
    init_cmd.input_file = pot
    init_cmd.output_file = localedir / f"{locale}.po"

    if init_cmd.output_file.exists() and not force:
        update_cmd = f"{ctx.parent.command_path} update" if ctx.parent else "update"
        msg = (
            f"Output file '{init_cmd.output_file}' already exists. Use '{update_cmd}' to update existing translations "
            f"or pass '--force' to overwrite."
        )
        raise click.ClickException(msg)

    init_cmd.ensure_finalized()
    init_cmd.run()


def _init_in_source_dir(ctx: click.Context, package: PackageSource, locale: Bcp47LanguageTag, *, force: bool) -> None:
    domain = domain_of(package.config)

    pot_file = package.path / "locale" / f"{domain}.pot"
    if not pot_file.exists():
        ctx.invoke(extract, source=package.path)

    output_mo_file = package.path / "locale" / f"{locale}.po"
    if output_mo_file.exists() and not force:
        update_cmd = f"{ctx.parent.command_path} update" if ctx.parent else "update"
        msg = (
            f"Output file '{output_mo_file}' already exists. Use '{update_cmd}' to update existing translations "
            f"or pass '--force' to overwrite."
        )
        raise click.ClickException(msg)

    _init_explicit(ctx, pot_file, package.path / "locale", locale, force=force)


@click.command
@click.argument("pot_or_package", type=click.Path(exists=True, path_type=Path))
@click.argument("locales", nargs=-1)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Instead of ignoring or failing languages whose catalogs already exists, this flag will cause them to be "
    "overwritten. YOU WILL LOSE ALL TRANSLATIONS IN THOSE FILES. To update a catalog, use the `update` command.",
)
@click.pass_context
def init(ctx: click.Context, pot_or_package: Path, locales: Collection[Bcp47LanguageTag] = (), *, force: bool) -> None:
    """Create new catalogs (.po files) from a template (.pot file).

    POT_OR_PACKAGE can be a package source directory, in which case the template catalog (.pot file) file will be
    expected at the default path `<POT_OR_PACKAGE>/locale/<namespace>.<short_name>.pot`, or POT_OR_PACKAGE can specify
    an explicit template catalog to use.

    LOCALES can be used to specify the languages (in BCP 47 format) for which to create catalogs. When POT_OR_PACKAGE is
    a package source directory, LOCALES can be omitted to use all uninitialized the languages listed in the package
    config's `languages` field.
    """
    if pot_or_package.is_file() and pot_or_package.suffix == ".pot":
        if not locales:
            msg = "When initializing from an explicit .pot file, you must specify which locales to initialize."
            raise click.UsageError(msg)

        for locale in locales:
            _init_explicit(ctx, pot_or_package, pot_or_package.parent / f"{locale}.po", locale, force=force)

    elif pot_or_package.is_dir():
        package = PackageSource(pot_or_package)

        if not locales:
            locales = package.config.languages.copy()

            if not force:
                for _, already_present_locale, _ in package.discover_po_files():
                    locales.remove(already_present_locale)

            if not locales:
                update_cmd = f"{ctx.parent.command_path} update" if ctx.parent else "update"
                msg = (
                    f"The package contains no uninitialized locales. Use '{update_cmd} {package.path}' if you wish to "
                    f"update them."
                )
                raise ClickException(msg)

            click.echo(f"Will initialize PO files for locale(s) {', '.join(locales)}.")

        for locale in locales:
            _init_in_source_dir(ctx, package, locale, force=force)

    else:
        # TODO: Support zipped-up packages.
        msg = f"Expected .pot file or package source directory, got '{pot_or_package}'."
        raise click.ClickException(msg)
