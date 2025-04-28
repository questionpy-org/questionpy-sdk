#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk, HTTPUnprocessableEntity

from questionpy import OptionsFormValidationError
from questionpy_common.elements import OptionsFormDefinition
from questionpy_sdk.webserver.routes.options import routes


@pytest.mark.app_routes(routes)
async def test_get_options(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_form_definition.return_value = OptionsFormDefinition()
    resp = await client.get("/options")

    assert resp.status == HTTPOk.status_code
    data = await resp.json()
    assert data["general"] == []


@pytest.mark.app_routes(routes)
async def test_get_options_state(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_options_state.return_value = {"foo": "bar"}
    resp = await client.get("/options/state")

    assert resp.status == HTTPOk.status_code
    data = await resp.json()
    assert data["foo"] == "bar"


@pytest.mark.app_routes(routes)
async def test_post_options_state(client: TestClient, mock_controller: AsyncMock) -> None:
    resp = await client.post("/options/state", json={"foo": "bar"})

    assert resp.status == HTTPOk.status_code
    mock_controller.save_options_state.assert_awaited_once()


@pytest.mark.app_routes(routes)
async def test_post_options_state_validation_error(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.save_options_state.side_effect = OptionsFormValidationError({"some": "error"})
    resp = await client.post("/options/state", json={"foo": "bar"})

    assert resp.status == HTTPUnprocessableEntity.status_code
    data = await resp.json()
    assert data["some"] == "error"
