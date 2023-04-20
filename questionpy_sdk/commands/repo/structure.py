from pathlib import Path
from shutil import copy

import click

from questionpy_sdk.commands._helper import create_normalized_filename
from questionpy_sdk.commands.repo._helper import get_manifest, IndexCreator


@click.command()
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path, resolve_path=True))
@click.argument("out_path", type=click.Path(file_okay=False, dir_okay=False, path_type=Path, resolve_path=True))
def structure(root: Path, out_path: Path) -> None:
    """Normalizes ROOT and indexes every package.

    Creates a normalized folder structure in OUT_PATH based on every package inside ROOT.
    Each package in ROOT will be copied to `OUT_PATH/namespace/short_name/namespace-short_name-version.qpy`
    """
    index_creator = IndexCreator(out_path)

    # Go through every package inside directory.
    for path in root.rglob("*.qpy"):
        manifest = get_manifest(path)

        # Move file to appropriate directory.
        new_directory = out_path / manifest.namespace / manifest.short_name
        new_directory.mkdir(parents=True, exist_ok=True)

        new_path = Path(copy(path, new_directory / create_normalized_filename(manifest)))

        index_creator.add(new_path, manifest)

    # Create package index and metadata.
    index_creator.write()
