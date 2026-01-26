#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import AsyncIterable
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from questionpy_common.api.question import ScoringMethod
from questionpy_common.elements import OptionsFormDefinition, TextInputElement
from questionpy_sdk.webserver.controllers.question import OptionsStateResponse, QuestionController
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
    mock_worker.get_options_form.side_effect = (
        (
            OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
            {"foo": "foo value"},
        ),
        (
            OptionsFormDefinition(general=[TextInputElement(label="Bar", name="bar")]),
            {"bar": "bar value"},
        ),
    )
    questions = await controller.get_questions()

    assert questions == {
        "svyhZCg8": {"foo": "foo value"},
        "tKVJTdsv": {"bar": "bar value"},
    }


async def test_get_options_state(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.get_options_form.return_value = (
        OptionsFormDefinition(general=[TextInputElement(label="Foo", name="foo")]),
        {"foo": "Bar"},
    )
    options_state = await controller.get_options_state("QaKxpanc")

    mock_state_manager.read_question_state.assert_called_once()
    assert options_state == OptionsStateResponse(data={"foo": "Bar"}, is_new=False)


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
    assert options_state == OptionsStateResponse(data={"foo": "Bar"}, is_new=True)


async def test_save_options_state(
    controller: QuestionController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.create_question_from_options.return_value = QuestionCreated(
        lang="en", scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE, question_state="question_state"
    )
    await controller.save_options_state("QaKxpanc", {"foo": "Baz"})

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


async def test_add_file(controller: QuestionController, mock_state_manager: AsyncMock) -> None:
    async def mock_reader() -> AsyncIterable[bytes]:  # noqa: RUF029
        yield b"some test content"

    options_file = await controller.add_file("test_file.txt", "text/plain", mock_reader())

    mock_state_manager.add_options_file.assert_called_once()
    assert options_file.filename == "test_file.txt"
    assert options_file.mime_type == "text/plain"
    assert options_file.file_ref == "dbabd43828eccd27e3a109b58454e4ff43c8673e"
    assert options_file.size == 17
    assert options_file.path == "/"
    assert isinstance(options_file.uploaded_at, datetime)


async def test_get_file(controller: QuestionController, mock_state_manager: AsyncMock) -> None:
    expected_options_file = Mock()
    expected_file_manager = Mock()
    mock_state_manager.get_options_file.return_value = (expected_options_file, expected_file_manager)

    options_file, file_manager = await controller.get_file("QaKxpanc", "my_file_upload", "abcdef0123456")

    mock_state_manager.get_options_file.assert_called_once_with("QaKxpanc", "my_file_upload", "abcdef0123456")
    assert options_file == expected_options_file
    assert file_manager == expected_file_manager
