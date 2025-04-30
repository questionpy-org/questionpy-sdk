#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import click

from questionpy_sdk.commands._helper import get_package_location
from questionpy_sdk.constants import DEFAULT_STATE_STORAGE_PATH
from questionpy_sdk.get_webserver import get_webserver
from questionpy_sdk.watcher import Watcher
from questionpy_server.worker.runtime.package_location import DirPackageLocation, PackageLocation

if TYPE_CHECKING:
    from collections.abc import Coroutine


async def run_watcher(
    pkg_path: Path,
    pkg_location: DirPackageLocation,
    state_storage_path: Path,
    host: str,
    port: int,
    *,
    legacy_frontend: bool,
) -> None:
    async with Watcher(
        pkg_path, pkg_location, state_storage_path, host, port, legacy_frontend=legacy_frontend
    ) as watcher:
        await watcher.run_forever()


async def async_run(
    pkg_location: PackageLocation, state_storage_path: Path, host: str, port: int, *, legacy_frontend: bool
) -> None:
    async with get_webserver(pkg_location, state_storage_path, host, port, legacy_frontend=legacy_frontend):
        await asyncio.Event().wait()  # Run forever


@click.command()
@click.argument("package")
@click.option(
    "--state-storage-path",
    type=click.Path(path_type=Path, exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_STATE_STORAGE_PATH,
    envvar="QPY_STATE_STORAGE_PATH",
    show_default=True,
    help="State storage path to use.",
)
@click.option(
    "--host", "-H", "host", default="localhost", show_default=True, type=click.STRING, help="Host to listen on."
)
@click.option(
    "--port", "-p", "port", default=8080, show_default=True, type=click.IntRange(1024, 65535), help="Port to bind to."
)
@click.option("--watch", "-w", "watch", is_flag=True, help="Watch source directory and rebuild on changes.")
@click.option(
    "--legacy-frontend",
    "-l",
    "legacy_frontend",
    is_flag=True,
    help="Use legacy frontend. "
    "(This is a temporary option that is going to be removed once the new frontend is finalized.)",
)
def run(package: str, state_storage_path: Path, host: str, port: int, *, watch: bool, legacy_frontend: bool) -> None:
    """Run a package.

    \b
    PACKAGE can be:
    - a .qpy file,
    - a dist directory, or
    - a source directory (built on-the-fly).
    """  # noqa: D301
    pkg_path = Path(package).resolve()
    pkg_location = get_package_location(package, pkg_path)
    coro: Coroutine

    if watch:
        if not isinstance(pkg_location, DirPackageLocation) or pkg_path == pkg_location.path:
            msg = "The --watch option only works with source directories."
            raise click.BadParameter(msg)
        coro = run_watcher(pkg_path, pkg_location, state_storage_path, host, port, legacy_frontend=legacy_frontend)
    else:
        coro = async_run(pkg_location, state_storage_path, host, port, legacy_frontend=legacy_frontend)

    asyncio.run(coro)
