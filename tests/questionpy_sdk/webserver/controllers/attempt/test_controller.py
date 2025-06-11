#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from unittest.mock import AsyncMock, Mock

import pytest

from questionpy import AttemptModel, AttemptScoredModel, AttemptStartedModel, AttemptUi, ScoringCode
from questionpy_sdk.webserver.controllers.attempt import AttemptController, AttemptStatus
from questionpy_sdk.webserver.controllers.attempt.errors import InvalidAttributeValueError
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions, RenderErrorCollection


@pytest.fixture
def controller(mock_webserver: Mock) -> AttemptController:
    return AttemptController(mock_webserver)


async def test_get_attempt_started(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_state_manager.read_attempt_state.side_effect = FileNotFoundError
    mock_state_manager.read_score.side_effect = FileNotFoundError
    mock_state_manager.read_attempt_seed.side_effect = FileNotFoundError
    mock_worker.start_attempt.return_value = AttemptStartedModel(
        variant=1, lang="en", ui=AttemptUi(formulation=""), attempt_state="attempt_state"
    )
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"

    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt(display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_status == AttemptStatus.STARTED
    assert data.score is None
    mock_state_manager.write_attempt_state.assert_called_once_with("attempt_state")
    mock_state_manager.write_attempt_seed.assert_called_once()


async def test_get_attempt_scored(
    controller: AttemptController, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_worker.get_attempt.return_value = AttemptModel(variant=1, lang="en", ui=AttemptUi(formulation=""))
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"
    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt(display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_status == AttemptStatus.SCORED
    assert data.score == 1.0


async def test_get_attempt_in_progress(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_worker.get_attempt.return_value = AttemptModel(variant=1, lang="en", ui=AttemptUi(formulation=""))
    mock_state_manager.read_score.side_effect = FileNotFoundError
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"

    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt(display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_status == AttemptStatus.IN_PROGRESS
    assert data.score is None


async def test_get_attempt_render_errors(
    controller: AttemptController,
    mock_formulation_renderer: Mock,
    mock_worker: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_worker.get_attempt.return_value = AttemptModel(variant=1, lang="en", ui=AttemptUi(formulation=""))

    with monkeypatch.context() as mp:
        mp.setattr(
            "questionpy_sdk.webserver.controllers.attempt.errors.etree.QName",
            Mock(return_value=Mock(localname="some_elem")),
        )
        elem_mock = Mock(sourceline=10, prefix="some_prefix")
        error = InvalidAttributeValueError(elem_mock, "some_attr", "some_value")
        formulation_errors = RenderErrorCollection([error])
        mock_formulation_renderer.render = Mock(return_value=("<html>Formulation</html>", formulation_errors))

        with caplog.at_level(logging.INFO):
            data = await controller.get_attempt(QuestionDisplayOptions())

            assert data.render_errors["formulation"] == formulation_errors
            assert "1 error occurred while rendering" in caplog.text
            assert "Line 10" in caplog.text
            assert "InvalidAttributeValueError" in caplog.text
            assert (
                "Invalid value 'some_value' for attribute 'some_attr' on element 'some_prefix:some_elem'" in caplog.text
            )


async def test_save_attempt(controller: AttemptController, mock_state_manager: AsyncMock) -> None:
    test_data = {"foo": "bar"}
    await controller.save_attempt(test_data)

    mock_state_manager.write_last_attempt_data.assert_called_once_with(test_data)


async def test_reset_attempt(controller: AttemptController, mock_state_manager: AsyncMock) -> None:
    await controller.reset_attempt()

    mock_state_manager.delete_state.assert_called_once()


async def test_score_attempt(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.score_attempt.return_value = AttemptScoredModel(
        variant=1,
        lang="en",
        ui=AttemptUi(formulation=""),
        score=0.9,
        score_final=None,
        scoring_code=ScoringCode.AUTOMATICALLY_SCORED,
    )
    await controller.score_attempt()

    args, _ = mock_state_manager.write_score.call_args
    attempt_scored = args[0]
    assert attempt_scored.score == 0.9
