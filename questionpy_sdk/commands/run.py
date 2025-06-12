#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import click

from questionpy_sdk.commands._helper import get_package_location
from questionpy_sdk.constants import DEFAULT_STATE_STORAGE_PATH
from questionpy_sdk.watcher import Watcher
from questionpy_sdk.webserver import WebServer
from questionpy_sdk.webserver.server import WebServerArgs
from questionpy_server.worker.impl.subprocess import SubprocessWorker
from questionpy_server.worker.impl.thread import ThreadWorker
from questionpy_server.worker.runtime.package_location import DirPackageLocation

if TYPE_CHECKING:
    from collections.abc import Coroutine


async def run_watcher(pkg_path: Path, webserver_args: WebServerArgs) -> None:
    async with Watcher(pkg_path, **webserver_args) as watcher:
        await watcher.run_forever()


async def async_run(webserver_args: WebServerArgs) -> None:
    async with WebServer(**webserver_args):
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
    "--worker",
    "-W",
    "worker",
    type=click.Choice(("subprocess", "thread"), case_sensitive=False),
    default="subprocess" if WebServer.DEFAULT_WORKER_CLASS is SubprocessWorker else "thread",
    show_default=True,
    help="The worker implementation to use. Thread workers offer no isolation but may improve debugging experience.",
)
def run(
    package: str,
    state_storage_path: Path,
    host: str,
    port: int,
    *,
    watch: bool,
    worker: Literal["subprocess", "thread"],
) -> None:
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

    webserver_args = WebServerArgs(
        package_location=pkg_location,
        state_storage_path=state_storage_path,
        host=host,
        port=port,
        worker_class=ThreadWorker if worker == "thread" else SubprocessWorker,
    )

    if watch:
        if not isinstance(pkg_location, DirPackageLocation) or pkg_path == pkg_location.path:
            msg = "The --watch option only works with source directories."
            raise click.BadParameter(msg)
        coro = run_watcher(pkg_path, webserver_args)
    else:
        coro = async_run(webserver_args)

    asyncio.run(coro)
