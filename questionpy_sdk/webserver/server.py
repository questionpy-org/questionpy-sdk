#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

from questionpy_common.constants import MiB
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.middlewares.controller import inject_controller_middleware
from questionpy_sdk.webserver.middlewares.error import api_error_middleware, error_middleware
from questionpy_sdk.webserver.routes import api_routes
from questionpy_sdk.webserver.routes.frontend import routes as frontend_routes
from questionpy_sdk.webserver.state import StateManager
from questionpy_server import WorkerPool
from questionpy_server.worker.impl.thread import ThreadWorker
from questionpy_server.worker.runtime.package_location import PackageLocation

from .constants import API_PATH_PREFIX, USE_VITE_DEV_SERVER, WEBSERVER_KEY

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

log = logging.getLogger("questionpy-sdk:web-server")


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

        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._manifest: Manifest | None = None
        self.worker_pool: WorkerPool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)
        self._state_manager: StateManager | None = None

    async def start_server(self) -> None:
        if self._app:
            msg = "Web app is already running"
            raise RuntimeError(msg)

        self._app = self._create_webapp()
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self._host, self._port).start()
        self._print_status()

    async def stop_server(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            self._app = None
            self._runner = None

    async def run_forever(self) -> None:
        await self.start_server()
        await asyncio.Event().wait()  # run forever

    def _create_webapp(self) -> web.Application:
        app = web.Application()
        app[WEBSERVER_KEY] = self

        app.on_startup.append(self._on_startup)
        app.middlewares.append(inject_controller_middleware)
        app.middlewares.append(error_middleware)

        # API
        api_app = web.Application()
        api_app.middlewares.append(api_error_middleware)
        for routes in api_routes:
            api_app.add_routes(routes)
        app.add_subapp(API_PATH_PREFIX, api_app)

        # Frontend
        if USE_VITE_DEV_SERVER:
            # Reverse proxy dev server...
            from questionpy_sdk.webserver.middlewares.vite_dev import vite_devserver_middleware  # noqa: PLC0415

            app.middlewares.append(vite_devserver_middleware)
        else:
            # ...or serve static frontend
            app.add_routes(frontend_routes)

        return app

    async def _on_startup(self, app: web.Application) -> None:
        # Load manifest
        worker: Worker
        async with self.worker_pool.get_worker(self.package_location, 0, None) as worker:
            self._manifest = await worker.get_manifest()

        # Initialize state manager
        pkg_dirname = f"{self._manifest.namespace}-{self._manifest.short_name}-{self._manifest.version}"
        self._state_manager = StateManager(self._state_storage_root / pkg_dirname)

    def _print_status(self) -> None:
        if self._runner is None:
            msg = "Web app is not running"
            raise RuntimeError(msg)

        len_af_inet = 2
        len_af_inet6 = 4
        urls = []
        for addr in self._runner.addresses:
            # IPv4 (e.g., ('192.168.0.1', 8080))
            if len(addr) == len_af_inet:
                urls.append(f"http://{addr[0]}:{addr[1]}")
            # IPv6 (e.g., ('::1', 8080, 0, 0))
            elif len(addr) == len_af_inet6:
                urls.append(f"http://[{addr[0]}]:{addr[1]}")
            else:
                msg = f"Unknown address format: {addr}"
                raise ValueError(msg)

        log.info("Webserver started: %s", " ".join(urls))

    @property
    def app(self) -> web.Application:
        if self._app is None:
            msg = "Web app not initialized"
            raise RuntimeError(msg)

        return self._app

    @property
    def manifest(self) -> Manifest:
        if self._manifest is None:
            msg = "Web app not initialized"
            raise RuntimeError(msg)

        return self._manifest

    @property
    def state_manager(self) -> StateManager:
        if self._state_manager is None:
            msg = "Web app not initialized"
            raise RuntimeError(msg)

        return self._state_manager
