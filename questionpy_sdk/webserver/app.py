#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import aiohttp_jinja2
from aiohttp import web
from jinja2 import PackageLoader

from questionpy_common.constants import MiB
from questionpy_sdk.webserver.state_storage import QuestionStateStorage
from questionpy_server import WorkerPool
from questionpy_server.worker.runtime.package_location import PackageLocation
from questionpy_server.worker.worker.thread import ThreadWorker


class WebServer:
    def __init__(
        self,
        package_location: PackageLocation,
        state_storage_path: Path = Path(__file__).parent / "question_state_storage",
    ):
        # We import here so we don't have to work around circular imports.
        from questionpy_sdk.webserver.routes.attempt import routes as attempt_routes  # noqa: PLC0415
        from questionpy_sdk.webserver.routes.options import routes as options_routes  # noqa: PLC0415

        self.package_location = package_location
        self.state_storage = QuestionStateStorage(state_storage_path)

        self.web_app = web.Application()
        self.web_app.add_routes(attempt_routes)
        self.web_app.add_routes(options_routes)
        self.web_app.router.add_static("/static", Path(__file__).parent / "static")
        self.web_app[SDK_WEBSERVER_APP_KEY] = self

        jinja2_extensions = ["jinja2.ext.do"]
        aiohttp_jinja2.setup(self.web_app, loader=PackageLoader(__package__), extensions=jinja2_extensions)
        self.worker_pool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)

    def start_server(self) -> None:
        web.run_app(self.web_app)


SDK_WEBSERVER_APP_KEY = web.AppKey("sdk_webserver_app", WebServer)
