#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from pathlib import Path
from types import TracebackType
from typing import ClassVar, NotRequired, Self, TypedDict, Unpack

from aiohttp import web

from questionpy_common.constants import MiB
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.middlewares.controller import inject_controller_middleware
from questionpy_sdk.webserver.middlewares.error import api_error_middleware, error_middleware
from questionpy_sdk.webserver.routes import api_routes
from questionpy_sdk.webserver.routes.frontend import routes as frontend_routes
from questionpy_sdk.webserver.state import StateManager
from questionpy_server import WorkerPool
from questionpy_server.worker import Worker
from questionpy_server.worker.impl.subprocess import SubprocessWorker
from questionpy_server.worker.runtime.package_location import PackageLocation

from .constants import API_PATH_PREFIX, USE_VITE_DEV_SERVER, WEBSERVER_KEY

log = logging.getLogger("questionpy-sdk:web-server")


class WebServerArgs(TypedDict):
    package_location: PackageLocation
    state_storage_path: Path
    host: NotRequired[str]
    port: NotRequired[int]
    worker_class: NotRequired[type[Worker]]


class WebServer:
    DEFAULT_WORKER_CLASS: ClassVar[type[Worker]] = SubprocessWorker

    def __init__(self, **kwargs: Unpack[WebServerArgs]) -> None:
        self.package_location = kwargs["package_location"]
        self._state_storage_root = kwargs["state_storage_path"]
        self._host = kwargs.get("host", "localhost")
        self._port = kwargs.get("port", 8080)
        self._worker_class = kwargs.get("worker_class", self.DEFAULT_WORKER_CLASS)

        self._web_app: web.Application
        self._runner: web.AppRunner

        self._manifest: Manifest
        self._state_manager: StateManager
        self._worker_pool: WorkerPool

    async def __aenter__(self) -> Self:
        # Add worker pool
        self._worker_pool = await WorkerPool(1, 500 * MiB, worker_type=self._worker_class).__aenter__()

        # Load manifest
        worker: Worker
        async with self._worker_pool.get_worker(self.package_location, 0, None) as worker:
            self._manifest = await worker.get_manifest()

        # Initialize state manager
        pkg_dirname = f"{self._manifest.namespace}-{self._manifest.short_name}-{self._manifest.version}"
        self._state_manager = StateManager(self._state_storage_root / pkg_dirname)

        # Create web app
        self._app = self._create_webapp()
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self._host, self._port).start()
        self._print_status()

        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self._runner.cleanup()
        await self._worker_pool.__aexit__(exc_type, exc_val, exc_tb)

    def _create_webapp(self) -> web.Application:
        app = web.Application()
        app[WEBSERVER_KEY] = self

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

    def _print_status(self) -> None:
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
        return self._app

    @property
    def manifest(self) -> Manifest:
        return self._manifest

    @property
    def worker_pool(self) -> WorkerPool:
        return self._worker_pool

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager
