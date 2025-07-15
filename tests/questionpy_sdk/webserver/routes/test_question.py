#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk, HTTPUnprocessableEntity

from questionpy import OptionsFormValidationError
from questionpy_common.elements import OptionsFormDefinition
from questionpy_sdk.webserver.routes.question import routes


@pytest.mark.app_routes(routes)
async def test_get_question(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_form_definition.return_value = OptionsFormDefinition()

    async with client.get("/question/myuQ2JWl") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["general"] == []


@pytest.mark.app_routes(routes)
async def test_delete_question(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.delete("/question/myuQ2JWl") as resp:
        assert resp.status == HTTPOk.status_code
    mock_controller.delete_question.assert_awaited_once_with("myuQ2JWl")


@pytest.mark.app_routes(routes)
async def test_get_questions(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_questions.return_value = {"myuQ2JWl": {}, "xTXbLYfl": {}}

    async with client.get("/questions") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data == {"myuQ2JWl": {}, "xTXbLYfl": {}}


@pytest.mark.app_routes(routes)
async def test_get_question_state(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_options_state.return_value = {"foo": "bar"}

    async with client.get("/question/myuQ2JWl/state") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["foo"] == "bar"


@pytest.mark.app_routes(routes)
async def test_post_question_state(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/question/myuQ2JWl/state", json={"foo": "bar"}) as resp:
        assert resp.status == HTTPOk.status_code
    mock_controller.save_options_state.assert_awaited_once()


@pytest.mark.app_routes(routes)
async def test_post_question_state_validation_error(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.save_options_state.side_effect = OptionsFormValidationError({"some": "error"})

    async with client.post("/question/myuQ2JWl/state", json={"foo": "bar"}) as resp:
        assert resp.status == HTTPUnprocessableEntity.status_code
        data = await resp.json()
        assert data["some"] == "error"
