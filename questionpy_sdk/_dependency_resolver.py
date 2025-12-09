import asyncio
import bisect
import logging
from collections.abc import Iterable, Sequence
from itertools import chain
from pathlib import Path

from semver import Version

from questionpy_common import PackageNamespaceAndShortName
from questionpy_common.package_location import PackageLocation, ZipPackageLocation
from questionpy_common.version_specifiers import QPyDependencyVersionSpecifier
from questionpy_server.dependencies import AvailablePackageVersion, DynamicDependencyResolver, NoPackageWithHashError
from questionpy_server.hash import calculate_hash
from questionpy_server.utils.manifest import ManifestError, read_manifest_from_zip


class SdkDynamicDependencyResolver(DynamicDependencyResolver):
    def __init__(self, dirs: Sequence[Path]) -> None:
        self._dirs = dirs

        self._packages: dict[PackageNamespaceAndShortName, list[AvailablePackageVersion]] = {}
        self._locations: dict[str, PackageLocation] = {}

        qpy_file: Path
        for qpy_file in chain.from_iterable(dir_.glob("*.qpy") for dir_ in self._dirs):
            hash_ = calculate_hash(qpy_file)

            try:
                manifest = asyncio.run(read_manifest_from_zip(qpy_file))
            except ManifestError:
                _log.warning("Failed to read manifest of package '%s'", qpy_file, exc_info=True)
                continue

            apv = AvailablePackageVersion(manifest, hash_, Version.parse(manifest.version))

            versions = self._packages.setdefault(apv.manifest.nssn, [])
            bisect.insort(versions, apv, key=lambda p: p.manifest.version)
            if apv.hash not in self._locations:
                self._locations[apv.hash] = ZipPackageLocation(qpy_file.absolute(), hash_)

    def get_matching_versions(
        self,
        nssn: PackageNamespaceAndShortName,
        version_spec: QPyDependencyVersionSpecifier | None,
        *,
        include_prereleases: bool,
    ) -> Iterable[AvailablePackageVersion]:
        versions_for_nssn = self._packages.get(nssn, ())

        # We could speed this up with bisections, but it's probably not worth the effort.
        return [
            package_version
            for package_version in versions_for_nssn
            if (include_prereleases or package_version.version.prerelease is None)
            and (version_spec is None or version_spec.allows(package_version.version))
        ]

    async def get_package_location(self, hash_: str) -> PackageLocation:
        try:
            return self._locations[hash_]
        except KeyError as e:
            raise NoPackageWithHashError(hash_) from e


_log = logging.getLogger(__name__)
