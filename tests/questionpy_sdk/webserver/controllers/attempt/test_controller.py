#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from unittest.mock import AsyncMock, Mock

import pytest

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import AttemptModel, AttemptScoredModel, AttemptStartedModel, AttemptUi, ScoringCode
from questionpy_sdk.webserver.controllers.attempt import AttemptController
from questionpy_sdk.webserver.controllers.attempt.data import AttemptStatus
from questionpy_sdk.webserver.controllers.attempt.errors import InvalidAttributeValueError
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions, RenderErrorCollection


@pytest.fixture
def controller(mock_webserver: Mock) -> AttemptController:
    return AttemptController(mock_webserver)


async def test_get_attempt_started(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_state_manager.read_attempt_state.side_effect = webserver_errors.MissingAttemptStateError
    mock_state_manager.read_attempt_score.side_effect = webserver_errors.MissingAttemptScoreError
    mock_state_manager.read_attempt_seed.side_effect = webserver_errors.MissingAttemptSeedError
    mock_worker.get_loaded_packages = Mock(return_value=[])
    mock_worker.start_attempt.return_value = AttemptStartedModel(
        variant=1, lang="en", ui=AttemptUi(formulation=""), attempt_state="attempt_state"
    )
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"

    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt("QaKxpanc", "AepM0AFN", display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_data.attempt_status == AttemptStatus.STARTED
    assert data.attempt_data.score is None
    mock_state_manager.write_attempt_state.assert_called_once_with("QaKxpanc", "AepM0AFN", "attempt_state")
    mock_state_manager.write_attempt_seed.assert_called_once()


async def test_get_attempt_scored(
    controller: AttemptController, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_worker.get_loaded_packages = Mock(return_value=[])
    mock_worker.get_attempt.return_value = AttemptModel(variant=1, lang="en", ui=AttemptUi(formulation=""))
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"
    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt("QaKxpanc", "AepM0AFN", display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_data.attempt_status == AttemptStatus.SCORED
    assert data.attempt_data.score == 1.0


async def test_get_attempt_in_progress(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock, mock_jinja2_template: Mock
) -> None:
    mock_worker.get_loaded_packages = Mock(return_value=[])
    mock_worker.get_attempt.return_value = AttemptModel(variant=1, lang="en", ui=AttemptUi(formulation=""))
    mock_state_manager.read_attempt_score.side_effect = webserver_errors.MissingAttemptScoreError
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"

    display_opts = QuestionDisplayOptions(general_feedback=True, specific_feedback=True, right_answer=True, roles=[])
    data = await controller.get_attempt("QaKxpanc", "AepM0AFN", display_opts)

    mock_jinja2_template.render_async.assert_called_once()
    assert data.attempt_html == "<html>Attempt</html>"
    assert data.attempt_data.attempt_status == AttemptStatus.IN_PROGRESS
    assert data.attempt_data.score is None


async def test_get_attempt_render_errors(
    controller: AttemptController,
    mock_formulation_renderer: Mock,
    mock_worker: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_worker.get_loaded_packages = Mock(return_value=[])
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
            data = await controller.get_attempt("QaKxpanc", "AepM0AFN", QuestionDisplayOptions())

            assert data.render_errors["formulation"] == formulation_errors
            assert "1 error occurred while rendering" in caplog.text
            assert "Line 10" in caplog.text
            assert "InvalidAttributeValueError" in caplog.text
            assert (
                "Invalid value 'some_value' for attribute 'some_attr' on element 'some_prefix:some_elem'" in caplog.text
            )


async def test_get_attempts(controller: AttemptController, mock_jinja2_template: Mock) -> None:
    mock_jinja2_template.render_async.return_value = "<html>Attempt</html>"
    attempts = await controller.get_attempts("QaKxpanc")

    assert attempts["eTCRKiod"].attempt_state == "data-1"
    assert attempts["J2m-ALhD"].attempt_state == "data-2"
    assert len(attempts) == 2


async def test_save_attempt(controller: AttemptController, mock_state_manager: AsyncMock) -> None:
    test_data = {"foo": "bar"}
    await controller.save_attempt("QaKxpanc", "AepM0AFN", test_data)

    mock_state_manager.write_attempt_data.assert_called_once_with("QaKxpanc", "AepM0AFN", test_data)


async def test_delete_attempt(controller: AttemptController, mock_state_manager: AsyncMock) -> None:
    await controller.delete_attempt("QaKxpanc", "AepM0AFN")

    mock_state_manager.delete_attempt.assert_called_once_with("QaKxpanc", "AepM0AFN")


async def test_score_attempt(
    controller: AttemptController, mock_state_manager: AsyncMock, mock_worker: AsyncMock
) -> None:
    mock_worker.score_attempt.return_value = AttemptScoredModel(
        variant=1,
        lang="en",
        ui=AttemptUi(formulation=""),
        score=0.9,
        score_adjusted=None,
        scoring_code=ScoringCode.AUTOMATICALLY_SCORED,
    )
    await controller.score_attempt("QaKxpanc", "AepM0AFN")

    args, _ = mock_state_manager.write_attempt_score.call_args
    attempt_scored = args[2]
    assert attempt_scored.score == 0.9


@pytest.mark.parametrize(
    ("data_missing", "score_missing"),
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ],
)
async def test_clone_attempt(
    data_missing: bool, score_missing: bool, controller: AttemptController, mock_state_manager: AsyncMock
) -> None:
    if data_missing:
        mock_state_manager.read_attempt_data.side_effect = webserver_errors.MissingAttemptDataError
    if score_missing:
        mock_state_manager.read_attempt_score.side_effect = webserver_errors.MissingAttemptScoreError

    await controller.clone_attempt("QaKxpanc", "AepM0AFN", "Pei2ohya")

    args, _ = mock_state_manager.write_attempt_state.call_args
    assert args == ("QaKxpanc", "Pei2ohya", "attempt_state")

    args, _ = mock_state_manager.write_attempt_seed.call_args
    assert args == ("QaKxpanc", "Pei2ohya", 1234)

    if data_missing:
        mock_state_manager.write_attempt_data.assert_not_called()
    else:
        args, _ = mock_state_manager.write_attempt_data.call_args
        assert args == ("QaKxpanc", "Pei2ohya", {"answer": "42"})

    if score_missing:
        mock_state_manager.write_attempt_score.assert_not_called()
    else:
        args, _ = mock_state_manager.write_attempt_score.call_args
        assert args[0] == "QaKxpanc"
        assert args[1] == "Pei2ohya"
        assert args[2].scoring_code == ScoringCode.AUTOMATICALLY_SCORED
        assert args[2].score == 1.0


async def test_clone_attempt_duplicate(controller: AttemptController) -> None:
    with pytest.raises(webserver_errors.DuplicateAttemptError):
        await controller.clone_attempt("QaKxpanc", "AepM0AFN", "eTCRKiod")
