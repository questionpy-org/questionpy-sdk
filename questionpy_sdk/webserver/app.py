#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import asyncio
import logging
import traceback
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp_jinja2
from aiohttp import web
from aiohttp.typedefs import Handler
from jinja2 import PackageLoader

from questionpy_common.api.qtype import InvalidQuestionStateError
from questionpy_common.constants import MiB
from questionpy_common.manifest import Manifest
from questionpy_server import WorkerPool
from questionpy_server.worker.impl.thread import ThreadWorker
from questionpy_server.worker.runtime.package_location import PackageLocation

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

log = logging.getLogger("questionpy-sdk:web-server")


async def _extract_manifest(app: web.Application) -> None:
    webserver = app[SDK_WEBSERVER_APP_KEY]
    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        app[MANIFEST_APP_KEY] = await worker.get_manifest()


@web.middleware
async def _invalid_question_state_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    try:
        return await handler(request)
    except InvalidQuestionStateError as e:
        question_state = webserver.read_state_file(StateFilename.QUESTION_STATE)
        context = {"stacktrace": "".join(traceback.format_exception(e)), "manifest": request.app[MANIFEST_APP_KEY]}
        if question_state is not None:
            context["question_state"] = question_state
        return aiohttp_jinja2.render_template("invalid_question_state.html.jinja2", request, context, status=500)


class StateFilename(StrEnum):
    QUESTION_STATE = "question_state.txt"
    ATTEMPT_STATE = "attempt_state.txt"
    ATTEMPT_SEED = "attempt_seed.txt"
    SCORE = "score.json"
    LAST_ATTEMPT_DATA = "last_attempt_data.json"


DEFAULT_STATE_STORAGE_PATH = Path(__file__).parent / "question_state_storage"
DEFAULT_STATE_STORAGE_PATH = Path(__file__).parent / "question_state_storage"
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

        self._web_app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self.worker_pool: WorkerPool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)

    async def start_server(self) -> None:
        if self._web_app:
            msg = "Web app is already running"
            raise RuntimeError(msg)

        self._web_app = self._create_webapp()
        self._runner = web.AppRunner(self._web_app)
        await self._runner.setup()
        await web.TCPSite(self._runner, self._host, self._port).start()
        self._print_urls()

    async def stop_server(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            self._web_app = None
            self._runner = None

    async def run_forever(self) -> None:
        await self.start_server()
        await asyncio.Event().wait()  # run forever

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
        # We import here, so we don't have to work around circular imports.
        from questionpy_sdk.webserver.routes.attempt import routes as attempt_routes  # noqa: PLC0415
        from questionpy_sdk.webserver.routes.options import routes as options_routes  # noqa: PLC0415
        from questionpy_sdk.webserver.routes.worker import routes as worker_routes  # noqa: PLC0415

        app = web.Application()
        app[SDK_WEBSERVER_APP_KEY] = self

        app.add_routes(attempt_routes)
        app.add_routes(options_routes)
        app.add_routes(worker_routes)
        app.router.add_static("/static", Path(__file__).parent / "static")

        app.on_startup.append(_extract_manifest)
        app.middlewares.append(_invalid_question_state_middleware)

        jinja2_extensions = ["jinja2.ext.do"]
        aiohttp_jinja2.setup(app, loader=PackageLoader(__package__), extensions=jinja2_extensions)

        return app

    @cached_property
    def _package_state_dir(self) -> Path:
        if self._web_app is None:
            msg = "Web app not initialized"
            raise RuntimeError(msg)

        manifest = self._web_app[MANIFEST_APP_KEY]
        return self._state_storage_root / f"{manifest.namespace}-{manifest.short_name}-{manifest.version}"

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


SDK_WEBSERVER_APP_KEY = web.AppKey("sdk_webserver_app", WebServer)
MANIFEST_APP_KEY = web.AppKey("manifest", Manifest)
