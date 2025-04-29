#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk

from questionpy import DisplayRole
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions
from questionpy_sdk.webserver.routes import attempt


@pytest.mark.app_routes(attempt.routes)
async def test_get_attempt(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_attempt.return_value = {
        "attempt_html": "<html>Test</html>",
        "attempt_status": "STARTED",
    }

    params = (
        ("generalFeedback", "false"),
        ("roles", "PROCTOR"),
        ("roles", "DEVELOPER"),
    )

    async with client.get("/attempt", params=params) as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["attempt_html"] == "<html>Test</html>"
        assert data["attempt_status"] == "STARTED"

        args, _ = mock_controller.get_attempt.call_args
        display_options = args[0]
        assert isinstance(display_options, QuestionDisplayOptions)
        assert display_options.general_feedback is False
        assert len(display_options.roles) == 2
        assert DisplayRole.PROCTOR in display_options.roles
        assert DisplayRole.DEVELOPER in display_options.roles


@pytest.mark.app_routes(attempt.routes)
async def test_post_attempt(client: TestClient, mock_controller: AsyncMock) -> None:
    test_data = {"answer": "42"}

    async with client.post("/attempt", json=test_data) as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.save_attempt.assert_awaited_once_with(test_data)


@pytest.mark.app_routes(attempt.routes)
async def test_post_attempt_score(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/attempt/score") as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.score_attempt.assert_awaited_once()


@pytest.mark.app_routes(attempt.routes)
async def test_post_attempt_restart(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/attempt/restart") as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.reset_attempt.assert_awaited_once()
