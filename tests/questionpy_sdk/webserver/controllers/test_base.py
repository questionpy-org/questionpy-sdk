#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from questionpy_sdk.webserver import WebServer
from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_server.worker.runtime.package_location import FunctionPackageLocation


@pytest.mark.parametrize(
    ("name", "route_kwargs", "expected"),
    [
        ("attempt", {}, "/api/attempt"),
        ("attempt-score", {}, "/api/attempt/score"),
        ("attempt-restart", {}, "/api/attempt/restart"),
        (
            "file",
            {"namespace": "test_ns", "short_name": "test_package", "path": "static/test.txt"},
            "/api/file/test_ns/test_package/static/test.txt",
        ),
        ("manifest", {}, "/api/manifest"),
        ("options", {}, "/api/options"),
        ("options-state", {}, "/api/options/state"),
    ],
)
async def test_generate_api_url(
    name: str,
    route_kwargs: dict[str, str],
    expected: str,
    mock_worker_pool: tuple[Mock, MagicMock],
    mock_web_components: tuple[Mock, AsyncMock],
) -> None:
    location = FunctionPackageLocation("test")
    async with WebServer(package_location=location, state_storage_path=Path("/foo/bar")) as server:
        url = BaseController(server).generate_api_url(name, **route_kwargs)
        assert str(url) == expected
