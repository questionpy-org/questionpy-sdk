import itertools
import operator
import sys
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path

import babel.messages.frontend
import babel.messages.pofile
import click

from questionpy.i18n import GettextDomain
from questionpy_common.manifest import Bcp47LanguageTag
from questionpy_sdk._i18n_utils import bcp47_to_posix
from questionpy_sdk._package.source import PackageSource


def _update_domain(
    po_files: Iterable[tuple[GettextDomain, Bcp47LanguageTag, Path]],
    pot_path: Path,
) -> None:
    with pot_path.open("rb") as pot_fd:
        template_catalog = babel.messages.pofile.read_po(pot_fd)

    if isinstance(template_catalog.creation_date, datetime):
        now = datetime.now(template_catalog.creation_date.tzinfo)
        if now - template_catalog.creation_date > timedelta(hours=1):
            click.echo("Warning: .pot file is more than 1 hour old. Is it up-to-date?")

    for _, lang, path in po_files:
        cmd = babel.messages.frontend.UpdateCatalog()
        cmd.locale = bcp47_to_posix(lang)
        cmd.input_file = pot_path
        cmd.output_file = path

        cmd.ensure_finalized()
        cmd.run()


@click.command()
@click.argument("package", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-t",
    "--pot",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Use a different catalog template.",
    show_default="<PACKAGE>/locale/<namespace>.<short_name>.pot",
)
@click.option(
    "-d", "--domain", "only_domain", help="Only update catalogs for the given domain instead of all catalogs."
)
@click.pass_context
def update(
    ctx: click.Context, package: Path, pot: Path | None = None, only_domain: GettextDomain | None = None
) -> None:
    """Update catalogs (.po files) from updated catalog templates (.pot files).

    \b
    Examples:
        Update all .po files in the package source dir::

            questionpy-sdk i18n update my-package-source-dir/

        Update the .po files for a specific domain in the package source dir::

            questionpy-sdk i18n update --domain foo my-package-source-dir/

        Update the .po files for a specific domain from a .pot file in a non-standard location::

            questionpy-sdk i18n update my-package-source-dir/ --domain foo --pot template.pot
    """  # noqa: D301 (it's a click feature)
    package_source = PackageSource(package)
    pos_by_domain = {
        domain: list(pos)
        for domain, pos in itertools.groupby(package_source.discover_po_files(), operator.itemgetter(0))
    }

    pots_by_domain = dict(package_source.discover_pot_files())
    if pot:
        if not only_domain:
            # Assume the .pot filename still follows our convention of <domain>.pot.
            only_domain = GettextDomain(pot.stem)
        pots_by_domain[only_domain] = pot

    domains_to_update = {only_domain} if only_domain else {*pos_by_domain, *pots_by_domain}

    failed_count = 0
    for domain in domains_to_update:
        if domain not in pos_by_domain:
            init_cmd = f"{ctx.parent.command_path} init" if ctx.parent else "init"
            click.echo(f"No .po files for domain '{domain}' were found. Use '{init_cmd}' to create some.")
            failed_count += 1
        elif domain not in pots_by_domain:
            extract_cmd = f"{ctx.parent.command_path} extract" if ctx.parent else "extract"
            click.echo(
                f"No .pot file for domain '{domain}' was found. Use '{extract_cmd}' to create one or pass "
                f"'--pot {domain}.pot' if it is in a non-standard location."
            )
            failed_count += 1
        else:
            _update_domain(pos_by_domain[domain], pots_by_domain[domain])

    if failed_count == len(domains_to_update):
        # All failed, let's consider this an error.
        sys.exit(1)
