from bisect import insort
from datetime import datetime, timezone
from json import dump
from pathlib import Path
from gzip import open as gzip_open
from zipfile import ZipFile

from questionpy_server.misc import calculate_hash
from questionpy_server.repository.models import RepoPackageVersions, RepoPackageVersion, RepoMeta
from questionpy_server.utils.manfiest import ComparableManifest, semver_encoder


def get_manifest(path: Path) -> ComparableManifest:
    """Reads the manifest of a package.

    Args:
        path: path to the package

    Returns:
        manifest of the package
    """
    with ZipFile(path) as zip_file:
        raw_manifest = zip_file.read("qpy_manifest.json")
    return ComparableManifest.parse_raw(raw_manifest)


def add_package_version(packages: dict[str, RepoPackageVersions], root: Path, path: Path,
                        manifest: ComparableManifest) -> None:
    """Populates `package_versions` and handles packages with same identifier and different versions.

    Args:
        packages: dictionary where keys are the identifier of a package
        root: root directory of the repository
        path: path to the package inside `root`
        manifest: manifest of the package at `path`
    """
    # Create RepoPackageVersion.
    full_path = root / path
    version = RepoPackageVersion(
        version=str(manifest.version),
        api_version=manifest.api_version,
        path=path,
        size=full_path.stat().st_size,
        sha256=calculate_hash(full_path)
    )

    # Check if package already exists.
    if repo_package := packages.get(manifest.identifier):
        # Package already exists - add version to list.
        insort(repo_package.list, version)
        if repo_package.list[-1] == version:
            # Currently most recent version of package - use its manifest.
            repo_package.manifest = manifest
    else:
        # Package does not exist - create new entry.
        packages[manifest.identifier] = RepoPackageVersions(manifest=manifest, list=[version])


def write_packages(root: Path, packages: dict[str, RepoPackageVersions]) -> Path:
    """Writes the package index into a json-file and compresses it.

    Args:
        root: root directory of the repository
        packages: dictionary where keys are the identifier of a package

    Returns:
        path to the package index
    """
    index: list[dict] = []
    packages_path = root / "PACKAGES.json.gz"

    for package in packages.values():
        repo_package_dict = package.dict(exclude={"manifest": {"entrypoint"}})
        index.append(repo_package_dict)

    with gzip_open(packages_path, "wt") as gzip_file:
        dump(index, gzip_file, default=semver_encoder)

    return packages_path


def write_meta(root: Path) -> Path:
    """Creates and writes metadata of the current repository / package index.

    Args:
        root: root directory of the repository

    Returns:
        path to the metadata
    """
    index_path = root / "PACKAGES.json.gz"
    meta = RepoMeta(
        timestamp=datetime.now(timezone.utc),
        sha256=calculate_hash(index_path),
        size=index_path.stat().st_size
    )
    meta_path = root / "META.json"
    meta_path.write_text(meta.json())
    return meta_path
