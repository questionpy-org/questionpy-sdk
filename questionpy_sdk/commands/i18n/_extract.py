import os
from pathlib import Path
from typing import Literal

import babel.messages
import babel.messages.pofile
import click
from babel.messages.extract import extract_from_dir

from questionpy.i18n import domain_of
from questionpy_sdk.package.source import PackageSource

_BABEL_MAPPING = [("python/**.py", "python"), ("templates/**.j2", "jinja2")]
# See Babel's DEFAULT_KEYWORDS for comparison.
_BABEL_KEYWORDS: dict[str, tuple[int | tuple[int, Literal["c"]], ...]] = {
    # Full names
    "gettext": (1,),
    "ngettext": (1, 2),
    "pgettext": ((1, "c"), 2),
    "npgettext": ((1, "c"), 2, 3),
    "dgettext": (2,),
    "dngettext": (2, 3),
    "dpgettext": ((2, "c"), 3),
    "dnpgettext": ((2, "c"), 3, 4),
    # Short names encouraged by us
    "__": (1,),
    "n": (1, 2),
    "p": ((1, "c"), 2),
    "np": ((1, "c"), 2, 3),
    # No-op markers
    "gettext_noop": (1,),
    "ngettext_noop": (1, 2),
    "pgettext_noop": ((1, "c"), 2),
    "npgettext_noop": ((1, "c"), 2, 3),
    # We don't encourage '_' in Python, but it's the default in Jinja's i18n extension so people may be used to it.
    "_": (1,),
}


def _directory_filter(dir_path: str) -> bool:
    """By default, Babel also excludes dirs starting with `_`, which we don't want."""
    subdir = os.path.basename(dir_path)
    return subdir != "__pycache__" and not subdir.startswith(".")


@click.command
@click.argument("package", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    show_default="<PACKAGE>/locale/<namespace>.<short_name>.pot",
)
def extract(package: Path, output: Path | None = None) -> None:
    """Extract translatable strings from a package source directory to a catalog template (.pot) file."""
    # TODO: Support extraction from already-zipped-up packages.

    package_source = PackageSource(package)
    domain = domain_of(package_source.config)

    if not output:
        output = package / "locale" / f"{domain}.pot"
    output.parent.mkdir(parents=True, exist_ok=True)

    catalog = babel.messages.Catalog(
        domain=domain,
        project=package_source.config.identifier,
        version=package_source.config.version,
        msgid_bugs_address=package_source.config.author,
    )

    for filename, lineno, message, comments, context in extract_from_dir(
        package,
        _BABEL_MAPPING,
        comment_tags=("TRANSLATORS:",),
        strip_comment_tags=True,
        keywords=_BABEL_KEYWORDS,
        directory_filter=_directory_filter,
    ):
        catalog.add(message, None, [(filename, lineno)], auto_comments=comments, context=context)

    with output.open("wb") as outfile:
        babel.messages.pofile.write_po(outfile, catalog)

    click.echo(f"Catalog template has been written to {output}.")
