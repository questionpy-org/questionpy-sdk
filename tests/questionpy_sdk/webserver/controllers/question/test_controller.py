#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock, Mock

import pytest

from questionpy_common.api.question import ScoringMethod
from questionpy_common.elements import OptionsFormDefinition, TextInputElement
from questionpy_sdk.webserver.controllers.question import QuestionController
from questionpy_sdk.webserver.controllers.question.controller import OptionsStateResponse
from questionpy_sdk.webserver.errors import MissingQuestionStateError
from questionpy_server.models import QuestionCreated


@pytest.fixture
def controller(mock_webserver: Mock) -> QuestionController:
    return QuestionController(mock_webserver)


async def test_get_form_definition(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    form_definition = await controller.get_form_definition("QaKxpanc")

    mock_state_manager.read_question_state.assert_called_once()
    assert isinstance(form_definition.general[0], TextInputElement)


async def test_get_questions(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    questions = await controller.get_questions()

    assert questions["svyhZCg8"]["general[foo]"] == "Bar"
    assert questions["tKVJTdsv"]["general[foo]"] == "Bar"
    assert len(questions) == 2


async def test_get_options_state(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    options_state = await controller.get_options_state("QaKxpanc")

    mock_state_manager.read_question_state.assert_called_once()
    assert options_state == OptionsStateResponse(data={"general[foo]": "Bar"}, is_new=False)


async def test_get_options_state_new(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    mock_state_manager.read_question_state.side_effect = MissingQuestionStateError
    options_state = await controller.get_options_state("QaKxpanc")

    mock_state_manager.read_question_state.assert_called_once()
    assert options_state == OptionsStateResponse(data={"general[foo]": "Bar"}, is_new=True)


async def test_save_options_state(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.create_question_from_options.return_value = QuestionCreated(
        lang="en", scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE, question_state="question_state"
    )
    await controller.save_options_state("QaKxpanc", {"general[foo]": "Baz"})

    mock_state_manager.read_question_state.assert_called_once()
    mock_state_manager.write_question_state.assert_called_once_with("QaKxpanc", "question_state")
