from pathlib import Path

import babel.messages
import babel.messages.pofile
import click
from babel.messages.extract import extract_from_dir

from questionpy.i18n import domain_of
from questionpy_sdk.package.source import PackageSource

_BABEL_MAPPING = [("python/**.py", "python"), ("templates/**.j2", "jinja2")]


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
        package, _BABEL_MAPPING, comment_tags=("TRANSLATORS:",), strip_comment_tags=True
    ):
        catalog.add(message, None, [(filename, lineno)], auto_comments=comments, context=context)

    with output.open("wb") as outfile:
        babel.messages.pofile.write_po(outfile, catalog)

    click.echo(f"Catalog template has been written to {output}.")
