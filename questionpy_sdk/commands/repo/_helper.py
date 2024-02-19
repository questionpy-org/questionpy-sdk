#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from bisect import insort
from datetime import datetime, timezone
from gzip import open as gzip_open
from pathlib import Path
from zipfile import ZipFile

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_server.misc import calculate_hash
from questionpy_server.repository.models import RepoPackageVersions, RepoPackageVersion, RepoMeta, RepoPackageIndex
from questionpy_server.utils.manifest import ComparableManifest


def get_manifest(path: Path) -> ComparableManifest:
    """Reads the manifest of a package.

    Args:
        path: path to the package

    Returns:
        manifest of the package
    """
    with ZipFile(path) as zip_file:
        raw_manifest = zip_file.read(MANIFEST_FILENAME)
    return ComparableManifest.model_validate_json(raw_manifest)


class IndexCreator:
    """Handles the creation of the repository index and metadata."""
    def __init__(self, root: Path):
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._packages: dict[str, RepoPackageVersions] = {}

    def add(self, path: Path, manifest: ComparableManifest) -> None:
        """Adds a package to the repository index.

        Args:
            path: path to the package inside `root`
            manifest: manifest of the package at `path`
        """
        # Create RepoPackageVersion.
        version = RepoPackageVersion(
            version=str(manifest.version),
            api_version=manifest.api_version,
            path=str(path.relative_to(self._root)),
            size=path.stat().st_size,
            sha256=calculate_hash(path)
        )

        # Check if package already exists.
        if repo_package := self._packages.get(manifest.identifier):
            # Package already exists - add version to list.
            insort(repo_package.versions, version)
            if repo_package.versions[-1] == version:
                # Currently most recent version of package - use its manifest.
                repo_package.manifest = manifest
        else:
            # Package does not exist - create new entry.
            self._packages[manifest.identifier] = RepoPackageVersions(manifest=manifest, versions=[version])

    def _write_index(self) -> Path:
        """Writes the package index into a json-file and compresses it.

        Returns:
            path to the package index
        """
        packages: list[dict] = []
        packages_path = self._root / "PACKAGES.json.gz"

        for package in self._packages.values():
            repo_package_dict = package.model_dump(exclude={"manifest": {"entrypoint"}})
            packages.append(repo_package_dict)

        with gzip_open(packages_path, "wt") as gzip_file:
            index = RepoPackageIndex(packages=packages)
            gzip_file.write(index.model_dump_json())

        return packages_path

    def _write_meta(self) -> Path:
        """Creates and writes metadata of the current repository / package index.

        Returns:
            path to the metadata
        """
        index_path = self._root / "PACKAGES.json.gz"
        meta = RepoMeta(
            repository_schema_version=1,
            timestamp=datetime.now(timezone.utc),
            sha256=calculate_hash(index_path),
            size=index_path.stat().st_size,
        )
        meta_path = self._root / "META.json"
        meta_path.write_text(meta.model_dump_json())
        return meta_path

    def write(self) -> tuple[Path, Path]:
        """Writes the package index and metadata into the repository.

        Returns:
            path to the package index and metadata
        """
        return self._write_index(), self._write_meta()
