import itertools
import operator
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import babel.messages.frontend
import babel.messages.pofile
import click

from questionpy.i18n import domain_of
from questionpy_sdk.commands.i18n import extract
from questionpy_sdk.package.source import PackageSource


def _update_domain(ctx: click.Context, package: PackageSource, domain: str, po_files: list[tuple[str, str, Path]],
                   pot_file: Path | None = None) -> None:
    default_pot_path = package.path / "locale" / f"{domain}.pot"
    if not pot_file:
        pot_file = default_pot_path

    if not pot_file.exists():
        if pot_file.samefile(default_pot_path) and domain == domain_of(package.config):
            ctx.invoke(extract, package.path)
        else:
            msg = f"Template catalog '{pot_file}' not found."
            raise click.ClickException(msg)

    with pot_file.open("rb") as pot_fd:
        template_catalog = babel.messages.pofile.read_po(pot_fd)

    if isinstance(template_catalog.creation_date, datetime):
        now = datetime.now(template_catalog.creation_date.tzinfo)
        if now - template_catalog.creation_date > timedelta(hours=1):
            click.echo("Warning: .pot file is more than 1 hour old.")

    for (locale, _, po_file) in po_files:
        cmd = babel.messages.frontend.UpdateCatalog()
        cmd.locale = locale
        cmd.input_file = pot_file
        cmd.output_file = po_file

        cmd.ensure_finalized()
        cmd.run()


@click.command
@click.argument("package_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--pot", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--domain")
@click.pass_context
def update(ctx: click.Context, package_path: Path, pot: Path | None = None, domain: str | None = None) -> None:
    package = PackageSource(package_path)
    pos_by_domain = {domain: list(pos) for domain, pos in
                     itertools.groupby(package.discover_po_files(), operator.itemgetter(1))}

    if domain:
        if domain not in pos_by_domain:
            msg = f"Package '{package.path}' contains no PO files for domain '{domain}'."
            raise click.ClickException(msg)
        _update_domain(ctx, package, domain, pos_by_domain[domain], pot)
    else:
        for po_domain, po_files in pos_by_domain.items():
            _update_domain(ctx, package, po_domain, po_files, pot)
