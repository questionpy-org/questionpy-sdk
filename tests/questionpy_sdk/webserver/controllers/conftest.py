#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from questionpy import ScoreModel, ScoringCode
from questionpy_sdk.webserver.controllers.attempt.question_ui import RenderErrorCollection


@pytest.fixture
def mock_state_manager() -> AsyncMock:
    state_manager = AsyncMock()
    state_manager.read_question_state.return_value = "question_state"
    state_manager.read_attempt_state.return_value = "attempt_state"
    state_manager.read_attempt_seed.return_value = 1234
    state_manager.read_last_attempt_data.return_value = {"answer": "42"}
    state_manager.read_score.return_value = ScoreModel(
        scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=1.0, score_final=None
    )
    return state_manager


@pytest.fixture
def mock_formulation_renderer(monkeypatch: pytest.MonkeyPatch) -> Iterator[Mock]:
    formulation_renderer = Mock()
    formulation_renderer.render = Mock(return_value=("<html>Formulation</html>", RenderErrorCollection()))
    formulation_renderer_class = Mock(return_value=formulation_renderer)

    with monkeypatch.context() as mp:
        mp.setattr(
            "questionpy_sdk.webserver.controllers.attempt.controller.QuestionFormulationUIRenderer",
            formulation_renderer_class,
        )
        yield formulation_renderer


@pytest.fixture
def mock_renderer(monkeypatch: pytest.MonkeyPatch) -> Iterator[Mock]:
    ui_renderer = Mock()
    ui_renderer.render = Mock(return_value=("<html>Feedback</html>", RenderErrorCollection()))
    ui_renderer_class = Mock(return_value=ui_renderer)

    with monkeypatch.context() as mp:
        mp.setattr("questionpy_sdk.webserver.controllers.attempt.controller.QuestionUIRenderer", ui_renderer_class)
        yield ui_renderer


@pytest.fixture
def mock_jinja2_template(monkeypatch: pytest.MonkeyPatch) -> Iterator[Mock]:
    with monkeypatch.context() as mp:
        template_mock = Mock()
        template_mock.render_async = AsyncMock(return_value="")
        env_mock = Mock()
        env_mock.get_template = Mock(return_value=template_mock)
        mp.setattr("jinja2.PackageLoader", Mock())
        mp.setattr("jinja2.Environment", Mock(return_value=env_mock))
        yield template_mock


@pytest.fixture
def mock_webserver(
    mock_state_manager: AsyncMock,
    mock_worker_pool: tuple[Mock, MagicMock],
    mock_formulation_renderer: Mock,
    mock_renderer: Mock,
    mock_jinja2_template: Mock,
) -> Mock:
    webserver = Mock()
    webserver.state_manager = mock_state_manager
    webserver.worker_pool = mock_worker_pool[1]
    return webserver
