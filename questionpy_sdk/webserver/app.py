#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import traceback
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
from questionpy_server.worker.runtime.package_location import PackageLocation
from questionpy_server.worker.worker.thread import ThreadWorker

if TYPE_CHECKING:
    from questionpy_server.worker.worker import Worker


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
        question_state = webserver.load_question_state()
        context = {"stacktrace": "".join(traceback.format_exception(e)), "manifest": request.app[MANIFEST_APP_KEY]}
        if question_state is not None:
            context["question_state"] = question_state
        return aiohttp_jinja2.render_template("invalid_question_state.html.jinja2", request, context, status=500)


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
        self._state_storage_path = state_storage_path

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

    def save_question_state(self, question_state: str) -> None:
        self._state_storage_path.mkdir(parents=True, exist_ok=True)
        self._state_file_path.write_text(question_state)

    def load_question_state(self) -> str | None:
        path = self._state_file_path
        if path.exists():
            return path.read_text()
        return None

    def delete_question_state(self) -> None:
        self._state_file_path.unlink(missing_ok=True)

    @cached_property
    def _state_file_path(self) -> Path:
        manifest = self.web_app[MANIFEST_APP_KEY]
        return self._state_storage_path / f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.txt"

    def start_server(self) -> None:
        web.run_app(self.web_app)


SDK_WEBSERVER_APP_KEY = web.AppKey("sdk_webserver_app", WebServer)
MANIFEST_APP_KEY = web.AppKey("manifest", Manifest)
