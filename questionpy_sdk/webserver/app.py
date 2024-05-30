#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
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


class WebServer:
    def __init__(
        self,
        package_location: PackageLocation,
        state_storage_path: Path = Path(__file__).parent / "question_state_storage",
    ) -> None:
        # We import here, so we don't have to work around circular imports.
        from questionpy_sdk.webserver.routes.attempt import routes as attempt_routes  # noqa: PLC0415
        from questionpy_sdk.webserver.routes.options import routes as options_routes  # noqa: PLC0415
        from questionpy_sdk.webserver.routes.worker import routes as worker_routes  # noqa: PLC0415

        self.package_location = package_location
        self._state_storage_root = state_storage_path

        self.web_app = web.Application()
        self.web_app[SDK_WEBSERVER_APP_KEY] = self

        self.web_app.add_routes(attempt_routes)
        self.web_app.add_routes(options_routes)
        self.web_app.add_routes(worker_routes)
        self.web_app.router.add_static("/static", Path(__file__).parent / "static")

        self.web_app.on_startup.append(_extract_manifest)
        self.web_app.middlewares.append(_invalid_question_state_middleware)

        jinja2_extensions = ["jinja2.ext.do"]
        aiohttp_jinja2.setup(self.web_app, loader=PackageLoader(__package__), extensions=jinja2_extensions)
        self.worker_pool: WorkerPool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)

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

    def start_server(self) -> None:
        web.run_app(self.web_app)

    @cached_property
    def _package_state_dir(self) -> Path:
        manifest = self.web_app[MANIFEST_APP_KEY]
        return self._state_storage_root / f"{manifest.namespace}-{manifest.short_name}-{manifest.version}"


SDK_WEBSERVER_APP_KEY = web.AppKey("sdk_webserver_app", WebServer)
MANIFEST_APP_KEY = web.AppKey("manifest", Manifest)
