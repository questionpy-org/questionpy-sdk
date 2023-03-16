from pathlib import Path

import click

from questionpy_server.repository.models import RepoPackageVersions

from questionpy_sdk.commands.repo._helper import get_manifest, add_package_version, write_packages, write_meta


@click.command()
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path, resolve_path=True))
def index(root: Path) -> None:
    """Indexes every package inside ROOT."""

    repo_packages: dict[str, RepoPackageVersions] = {}

    # Go through every package inside directory.
    for path in root.rglob("*.qpy"):
        manifest = get_manifest(path)
        add_package_version(repo_packages, root, path, manifest)

    # Write package index and metadata.
    write_packages(root, repo_packages)
    write_meta(root)
