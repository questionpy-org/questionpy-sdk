#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Awaitable, Callable, Iterator
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient


@pytest.fixture
async def client(
    request: pytest.FixtureRequest, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]]
) -> TestClient:
    marker = request.node.get_closest_marker("app_routes")

    if marker is None:
        pytest.fail("Test requires @pytest.mark.app_routes")

    app = web.Application()
    app.add_routes(marker.args[0])
    return await aiohttp_client(app)


@pytest.fixture
def mock_controller(monkeypatch: pytest.MonkeyPatch) -> Iterator[AsyncMock]:
    with monkeypatch.context() as mp:
        mock = AsyncMock()
        mp.setattr("questionpy_sdk.webserver.routes.base.BaseView.controller", property(lambda self: mock))
        yield mock
