#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock, Mock

import pytest

from questionpy_common.api.question import ScoringMethod
from questionpy_common.elements import OptionsFormDefinition, TextInputElement
from questionpy_sdk.webserver.controllers.options import OptionsController
from questionpy_server.models import QuestionCreated


@pytest.fixture
def controller(mock_webserver: Mock) -> OptionsController:
    return OptionsController(mock_webserver)


async def test_get_form_definition(
    controller: OptionsController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    form_definition = await controller.get_form_definition()

    mock_state_manager.read_question_state.assert_called_once()
    assert isinstance(form_definition.general[0], TextInputElement)


async def test_get_options_state(
    controller: OptionsController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    options_state = await controller.get_options_state()

    mock_state_manager.read_question_state.assert_called_once()
    assert options_state == {"general[foo]": "Bar"}


async def test_save_options_state(
    controller: OptionsController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.create_question_from_options.return_value = QuestionCreated(
        lang="en", scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE, question_state="question_state"
    )
    await controller.save_options_state({"general[foo]": "Baz"})

    mock_state_manager.read_question_state.assert_called_once()
    mock_state_manager.write_question_state.assert_called_once_with("question_state")
