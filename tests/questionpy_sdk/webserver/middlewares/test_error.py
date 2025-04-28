#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Awaitable, Callable

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPBadRequest, HTTPForbidden, HTTPInternalServerError
from pydantic import BaseModel

from questionpy_sdk.webserver.middlewares.error import api_error_middleware, error_middleware


@pytest.fixture
def some_error_route(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
) -> web.RouteTableDef:
    class SomeError(Exception):
        pass

    routes = web.RouteTableDef()

    @routes.view("/")
    class View(web.View):
        async def get(self) -> web.Response:
            raise SomeError

    app.add_routes(routes)
    return routes


@pytest.fixture
def http_forbidden_route(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
) -> web.RouteTableDef:
    routes = web.RouteTableDef()

    @routes.view("/")
    class View(web.View):
        async def get(self) -> web.Response:
            raise web.HTTPForbidden

    app.add_routes(routes)
    return routes


async def test_api_error_middleware_validation_error(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
) -> None:
    routes = web.RouteTableDef()

    class SomeModel(BaseModel):
        some_str: str

    @routes.view("/")
    class View(web.View):
        async def get(self) -> web.Response:
            return web.json_response(text=SomeModel(some_str=42).model_dump_json())

    app.add_routes(routes)
    app.middlewares.append(api_error_middleware)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPBadRequest.status_code
        data = await resp.json()
        assert data["error"] == "ValidationError"
        assert len(data["details"]) == 1
        assert data["details"][0]["input"] == 42


async def test_api_error_middleware_internal_server_error(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    some_error_route: web.RouteTableDef,
) -> None:
    app.middlewares.append(api_error_middleware)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPInternalServerError.status_code
        data = await resp.json()
        assert data["error"] == "SomeError"
        assert "Traceback" in data["details"]
        assert "SomeError" in data["details"]


async def test_api_error_middleware_pass_through(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    http_forbidden_route: web.RouteTableDef,
) -> None:
    app.middlewares.append(api_error_middleware)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPForbidden.status_code
        data = await resp.json()
        assert "Forbidden" in data["error"]


async def test_error_middleware_internal_server_error(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    some_error_route: web.RouteTableDef,
) -> None:
    app.middlewares.append(error_middleware)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPInternalServerError.status_code
        text = await resp.text()
        assert "Traceback" in text
        assert "SomeError" in text


async def test_error_middleware_pass_through(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    http_forbidden_route: web.RouteTableDef,
) -> None:
    app.middlewares.append(error_middleware)
    client = await aiohttp_client(app)

    async with client.get("/") as resp:
        assert resp.status == HTTPForbidden.status_code
