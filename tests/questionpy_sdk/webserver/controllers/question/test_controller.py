#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import AsyncMock, Mock

import pytest

from questionpy_common.api.question import ScoringMethod
from questionpy_common.elements import OptionsFormDefinition, TextInputElement
from questionpy_sdk.webserver.controllers.question import QuestionController
from questionpy_sdk.webserver.controllers.question.controller import OptionsStateResponse
from questionpy_sdk.webserver.errors import DuplicateQuestionError, MissingQuestionStateError
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


async def test_get_questions(controller: QuestionController, mock_worker: AsyncMock) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    questions = await controller.get_questions()

    question_1 = questions["svyhZCg8"]
    assert isinstance(question_1, dict)
    assert question_1["general[foo]"] == "Bar"

    question_2 = questions["tKVJTdsv"]
    assert isinstance(question_2, dict)
    assert question_2["general[foo]"] == "Bar"

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


async def test_clone_question(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    await controller.clone_question("QaKxpanc", "Bu2boh5u")

    mock_state_manager.read_question_state.assert_called_once()
    mock_state_manager.write_question_state.assert_called_once_with("Bu2boh5u", "question_state")


async def test_clone_question_duplicate(controller: QuestionController, mock_state_manager: AsyncMock) -> None:
    with pytest.raises(DuplicateQuestionError):
        await controller.clone_question("QaKxpanc", "tKVJTdsv")
