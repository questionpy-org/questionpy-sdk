#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import click

from questionpy_sdk.commands.repo._helper import get_manifest, IndexCreator


@click.command()
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path, resolve_path=True))
def index(root: Path) -> None:
    """Indexes every package inside ROOT."""
    index_creator = IndexCreator(root)

    # Go through every package inside directory.
    for path in root.rglob("*.qpy"):
        manifest = get_manifest(path)
        index_creator.add(path, manifest)

    # Write package index and metadata.
    index_creator.write()
