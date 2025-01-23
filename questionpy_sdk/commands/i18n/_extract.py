from pathlib import Path

import babel.messages
import babel.messages.pofile
import click
from babel.messages.extract import extract_from_dir

from questionpy.i18n import domain_of
from questionpy_sdk.package.source import PackageSource

_BABEL_MAPPING = [("python/**.py", "python"), ("templates/**.j2", "jinja2")]


@click.command
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path))
def extract(source: Path, output: Path | None = None) -> None:
    # TODO: Support extraction from already-zipped-up packages.

    package = PackageSource(source)
    domain = domain_of(package.config)

    if not output:
        output = source / "locale" / f"{domain}.pot"
    output.parent.mkdir(parents=True, exist_ok=True)

    catalog = babel.messages.Catalog(
        domain=domain,
        project=package.config.identifier,
        version=package.config.version,
        msgid_bugs_address=package.config.author,
    )

    for filename, lineno, message, comments, context in extract_from_dir(
        source, _BABEL_MAPPING, comment_tags=("TRANSLATORS:",), strip_comment_tags=True
    ):
        catalog.add(message, None, [(filename, lineno)], auto_comments=comments, context=context)

    with output.open("wb") as outfile:
        babel.messages.pofile.write_po(outfile, catalog)

    click.echo(f"Catalog template has been written to {output}.")
