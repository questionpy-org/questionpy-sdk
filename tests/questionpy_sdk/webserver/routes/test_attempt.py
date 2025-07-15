#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk

from questionpy import DisplayRole
from questionpy_sdk.webserver.controllers.attempt.controller import AttemptRenderData
from questionpy_sdk.webserver.controllers.attempt.data import AttemptData, AttemptStatus
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions
from questionpy_sdk.webserver.routes import attempt


@pytest.mark.app_routes(attempt.routes)
async def test_get_attempt(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_attempt.return_value = AttemptRenderData(
        attempt_data=AttemptData(
            attempt_status=AttemptStatus.STARTED,
            attempt_state="some_state",
            variant=0,
        ),
        attempt_html="<html>Test</html>",
        render_errors={},
    )

    params = (
        ("general_feedback", "false"),
        ("roles", "PROCTOR"),
        ("roles", "DEVELOPER"),
    )

    async with client.get("/question/myuQ2JWl/attempt/UY9ryXzq", params=params) as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["attempt_data"]["attempt_status"] == "STARTED"
        assert data["attempt_data"]["attempt_state"] == "some_state"
        assert data["attempt_data"]["variant"] == 0
        assert data["attempt_html"] == "<html>Test</html>"
        assert data["render_errors"] == {}

    args, _ = mock_controller.get_attempt.call_args
    question_id, attempt_id, display_options = args

    assert question_id == "myuQ2JWl"
    assert attempt_id == "UY9ryXzq"
    assert isinstance(display_options, QuestionDisplayOptions)
    assert display_options.general_feedback is False
    assert display_options.specific_feedback is True
    assert len(display_options.roles) == 2
    assert DisplayRole.PROCTOR in display_options.roles
    assert DisplayRole.DEVELOPER in display_options.roles


@pytest.mark.app_routes(attempt.routes)
async def test_post_attempt(client: TestClient, mock_controller: AsyncMock) -> None:
    test_data = {"answer": "42"}

    async with client.post("/question/myuQ2JWl/attempt/UY9ryXzq", json=test_data) as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.save_attempt.assert_awaited_once_with("myuQ2JWl", "UY9ryXzq", test_data)


@pytest.mark.app_routes(attempt.routes)
async def test_delete_attempt(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.delete("/question/myuQ2JWl/attempt/UY9ryXzq") as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.delete_attempt.assert_awaited_once_with("myuQ2JWl", "UY9ryXzq")


@pytest.mark.app_routes(attempt.routes)
async def test_get_attempts(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_attempts.return_value = {
        "UY9ryXzq": AttemptData(attempt_status=AttemptStatus.SCORED, attempt_state="data", variant=1),
    }

    async with client.get("/question/myuQ2JWl/attempts") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data == {
            "UY9ryXzq": {
                "attempt_status": "SCORED",
                "attempt_state": "data",
                "variant": 1,
                "score": None,
                "scoring_code": None,
                "scoring_state": None,
            }
        }


@pytest.mark.app_routes(attempt.routes)
async def test_post_attempt_score(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/question/myuQ2JWl/attempt/UY9ryXzq/score") as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.score_attempt.assert_awaited_once_with("myuQ2JWl", "UY9ryXzq")
