#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import logging
from zipfile import ZipFile

from pydantic import ByteSize

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME, MAX_MANIFEST_SIZE
from questionpy_common.manifest import Manifest
from questionpy_server.worker.runtime.package_location import (
    DirPackageLocation,
    FunctionPackageLocation,
    PackageLocation,
    ZipPackageLocation,
)

log = logging.getLogger("questionpy-sdk:manifest")


def _read_manifest_sync(location: PackageLocation) -> Manifest:
    if isinstance(location, FunctionPackageLocation):
        return location.manifest

    if isinstance(location, ZipPackageLocation | DirPackageLocation):
        if isinstance(location, ZipPackageLocation):
            with ZipFile(location.path) as zip_file:
                data = zip_file.read(f"{DIST_DIR}/{MANIFEST_FILENAME}")
        else:
            data = (location.path / MANIFEST_FILENAME).read_bytes()

        size = len(data)
        if size > MAX_MANIFEST_SIZE:
            log.warning(
                "The manifest has a size of %s which is larger than the maximum allowed size of %s.",
                ByteSize(size).human_readable(),
                MAX_MANIFEST_SIZE.human_readable(),
            )

        return Manifest.model_validate_json(data)

    msg = f"Unknown package location: '{location}'"
    raise ValueError(msg)


async def read_manifest(location: PackageLocation) -> Manifest:
    """Read the manifest from a package location."""
    return await asyncio.to_thread(_read_manifest_sync, location)
