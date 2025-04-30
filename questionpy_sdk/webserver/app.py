#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from functools import cached_property
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Self

from aiohttp import web

from questionpy_common.constants import MiB
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.routes.api import serve_api
from questionpy_sdk.webserver.routes.frontend import serve_frontend
from questionpy_server import WorkerPool
from questionpy_server.worker.impl.thread import ThreadWorker
from questionpy_server.worker.runtime.package_location import PackageLocation

from .constants import WEBSERVER_KEY, StateFilename

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

log = logging.getLogger("questionpy-sdk:web-server")

LEN_AF_INET = 2
LEN_AF_INET6 = 4


class WebServer:
    def __init__(
        self,
        package_location: PackageLocation,
        state_storage_path: Path,
        host: str = "localhost",
        port: int = 8080,
    ) -> None:
        self.package_location = package_location
        self._state_storage_root = state_storage_path
        self._host = host
        self._port = port

        self._web_app: web.Application
        self._runner: web.AppRunner
        self._manifest: Manifest
        self._worker_pool: WorkerPool

    async def __aenter__(self) -> Self:
        # Worker pool
        self._worker_pool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)

        # Load manifest
        worker: Worker
        async with self._worker_pool.get_worker(self.package_location, 0, None) as worker:
            self._manifest = await worker.get_manifest()

        self._web_app = self._create_webapp()
        self._runner = web.AppRunner(self._web_app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self._host, self._port).start()
        self._print_urls()

        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self._runner.cleanup()
        await self._worker_pool.__aexit__(exc_type, exc_val, exc_tb)

    def read_state_file(self, filename: StateFilename) -> str | None:
        try:
            return (self._package_state_dir / filename).read_text()
        except FileNotFoundError:
            return None

    def write_state_file(self, filename: StateFilename, data: str) -> None:
        self._package_state_dir.mkdir(parents=True, exist_ok=True)
        (self._package_state_dir / filename).write_text(data)

    def delete_state_files(self, filename_1: StateFilename, *filenames: StateFilename) -> None:
        for filename in (filename_1, *filenames):
            (self._package_state_dir / filename).unlink(missing_ok=True)
        if not any(self._package_state_dir.iterdir()):
            # Remove package state dir if it's now empty.
            self._package_state_dir.rmdir()

    def _create_webapp(self) -> web.Application:
        app = web.Application()
        app[WEBSERVER_KEY] = self

        serve_api(app)
        serve_frontend(app)

        return app

    @cached_property
    def _package_state_dir(self) -> Path:
        if self._web_app is None:
            msg = "Web app not initialized"
            raise RuntimeError(msg)

        manifest = self.manifest
        return self._state_storage_root / f"{manifest.namespace}-{manifest.short_name}-{manifest.version}"

    @property
    def manifest(self) -> Manifest:
        return self._manifest

    @property
    def worker_pool(self) -> WorkerPool:
        return self._worker_pool

    def _print_urls(self) -> None:
        if self._runner is None:
            msg = "Web app is not running"
            raise RuntimeError(msg)

        urls = []
        for addr in self._runner.addresses:
            # IPv4 (e.g., ('192.168.0.1', 8080))
            if len(addr) == LEN_AF_INET:
                urls.append(f"http://{addr[0]}:{addr[1]}")
            # IPv6 (e.g., ('::1', 8080, 0, 0))
            elif len(addr) == LEN_AF_INET6:
                urls.append(f"http://[{addr[0]}]:{addr[1]}")
            else:
                msg = f"Unknown address format: {addr}"
                raise ValueError(msg)

        log.info("Webserver started: %s", " ".join(urls))
