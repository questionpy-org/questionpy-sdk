#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk

from questionpy_common.manifest import Bcp47LanguageTag, Manifest
from questionpy_sdk.webserver.routes.manifest import routes


@pytest.mark.app_routes(routes)
async def test_get_manifest(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_manifest = Mock()
    mock_controller.get_manifest.return_value = Manifest(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="Jane Doe <jane.doe@example.org>",
        name={Bcp47LanguageTag("en"): "Test Package"},
        languages=[Bcp47LanguageTag("de"), Bcp47LanguageTag("en")],
    )

    async with client.get("/manifest") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["short_name"] == "foo"
        assert data["version"] == "0.0.1"
