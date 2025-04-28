#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Awaitable, Callable

from aiohttp import web
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk

from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_sdk.webserver.middlewares.controller import inject_controller_middleware
from questionpy_sdk.webserver.routes.base import BaseView


async def test_inject_controller_middleware(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
) -> None:
    class Controller(BaseController):
        def get_some_data(self) -> str:
            return "dummy data"

    routes = web.RouteTableDef()

    @routes.view("/")
    class View(BaseView["Controller"]):
        controller_class = Controller

        async def get(self) -> web.Response:
            assert isinstance(self.controller, Controller)
            return web.Response(text=self.controller.get_some_data())

    app.middlewares.append(inject_controller_middleware)
    app.add_routes(routes)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPOk.status_code
        assert await resp.text() == "dummy data"
