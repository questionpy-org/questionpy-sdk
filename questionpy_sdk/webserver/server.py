#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
import os
from pathlib import Path
from types import TracebackType
from typing import ClassVar, Literal, NotRequired, Self, TypedDict, Unpack

from aiohttp import web

from questionpy_common.environment import PackagePermissions
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.middlewares.controller import inject_controller_middleware
from questionpy_sdk.webserver.middlewares.error import api_error_middleware, error_middleware
from questionpy_sdk.webserver.routes import api_routes
from questionpy_sdk.webserver.routes.frontend import routes as frontend_routes
from questionpy_sdk.webserver.state import FilesystemStateManager, StateManager
from questionpy_server import WorkerPool
from questionpy_server.settings import CompletePackagePermissions
from questionpy_server.worker import Worker
from questionpy_server.worker.impl.subprocess import SubprocessWorker
from questionpy_server.worker.runtime.package_location import PackageLocation

from .constants import API_PATH_PREFIX, USE_VITE_DEV_SERVER, WEBSERVER_KEY
from .errors import EnvironmentVariablesMissingError
from .manifest import read_manifest

log = logging.getLogger("questionpy-sdk:web-server")

type AccessLogMode = Literal["all", "api", "none"]


class WebServerArgs(TypedDict):
    package_location: PackageLocation
    state_storage_path: Path
    host: NotRequired[str]
    port: NotRequired[int]
    worker_class: NotRequired[type[Worker]]
    access_log_mode: NotRequired[AccessLogMode]


class FilteredAccessLogger(web.AccessLogger):
    mode: AccessLogMode = "api"

    def log(self, request: web.BaseRequest, response: web.StreamResponse, time: float) -> None:
        if self.mode == "none":
            return
        if self.mode == "api" and not request.path.startswith(f"{API_PATH_PREFIX}/"):
            return

        super().log(request, response, time)


class WebServer:
    DEFAULT_WORKER_CLASS: ClassVar[type[Worker]] = SubprocessWorker

    def __init__(self, **kwargs: Unpack[WebServerArgs]) -> None:
        self.package_location = kwargs["package_location"]
        self._state_storage_root = kwargs["state_storage_path"]
        self._host = kwargs.get("host", "localhost")
        self._port = kwargs.get("port", 8080)
        self._worker_class = kwargs.get("worker_class", self.DEFAULT_WORKER_CLASS)
        self._access_log_mode = kwargs.get("access_log_mode", "api")

        self._app: web.Application
        self._api_app: web.Application
        self._runner: web.AppRunner

        self._manifest: Manifest
        self._state_manager: StateManager
        self._worker_pool: WorkerPool
        self._package_permissions: PackagePermissions

    async def __aenter__(self) -> Self:
        # Read manifest
        self._manifest = await read_manifest(self.package_location)

        # Check if required environment variables are set
        requested_environment_variables = self._manifest.environment_variables or set()
        if missing_environment_variables := requested_environment_variables - os.environ.keys():
            raise EnvironmentVariablesMissingError(missing=missing_environment_variables)

        # Assemble worker permissions
        permissions = CompletePackagePermissions()
        if self._manifest.permissions:
            permissions = permissions.model_copy(update=self._manifest.permissions.model_dump(exclude_none=True))
        self._package_permissions = PackagePermissions(**permissions.model_dump())

        # Add worker pool
        self._worker_pool = await WorkerPool(
            max_workers=1, max_memory=self._package_permissions.memory, worker_type=self._worker_class
        ).__aenter__()

        # Initialize state manager
        pkg_dirname = f"{self._manifest.namespace}-{self._manifest.short_name}-{self._manifest.version}"
        self._state_manager = FilesystemStateManager(self._state_storage_root / pkg_dirname)

        # Create web app
        self._app = self._create_webapp()
        FilteredAccessLogger.mode = self._access_log_mode
        self._runner = web.AppRunner(self.app, access_log=log, access_log_class=FilteredAccessLogger)
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
        self._api_app = web.Application()
        self._api_app.middlewares.append(api_error_middleware)
        for routes in api_routes:
            self._api_app.add_routes(routes)
        app.add_subapp(API_PATH_PREFIX, self._api_app)

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
    def api_app(self) -> web.Application:
        return self._api_app

    @property
    def manifest(self) -> Manifest:
        return self._manifest

    @property
    def worker_pool(self) -> WorkerPool:
        return self._worker_pool

    @property
    def package_permissions(self) -> PackagePermissions:
        return self._package_permissions

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager
