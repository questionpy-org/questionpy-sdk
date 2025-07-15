#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import ScoreModel, ScoringCode
from questionpy_sdk.webserver.state import FilesystemStateManager, StateManager

if TYPE_CHECKING:
    from pydantic import JsonValue


@pytest.fixture
def state_manager(tmp_path: Path) -> StateManager:
    return FilesystemStateManager(tmp_path)


async def test_read_question_states(state_manager: StateManager) -> None:
    await state_manager.write_question_state("myuQ2JWl", "data1")
    await state_manager.write_question_state("nYKEjBaA", "data2")
    await state_manager.write_question_state("5YfGRyRs", "data3")
    result = await state_manager.read_question_states()

    assert result["myuQ2JWl"] == "data1"
    assert result["nYKEjBaA"] == "data2"
    assert result["5YfGRyRs"] == "data3"
    assert len(result) == 3


async def test_read_question_state(state_manager: StateManager) -> None:
    test_data = "question state data"
    await state_manager.write_question_state("myuQ2JWl", test_data)
    result = await state_manager.read_question_state("myuQ2JWl")

    assert result == test_data


async def test_read_question_state_missing_file_raises(state_manager: StateManager) -> None:
    with pytest.raises(webserver_errors.MissingQuestionStateError):
        await state_manager.read_question_state("myuQ2JWl")


async def test_delete_question(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_question_state("myuQ2JWl", "question data")
    await state_manager.write_attempt_state("myuQ2JWl", "UY9ryXzq", "attempt data")
    await state_manager.delete_question("myuQ2JWl")

    assert not (tmp_path / "myuQ2JWl").exists()


async def test_delete_question_leaves_other_files(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_question_state("myuQ2JWl", "data")
    (tmp_path / "myuQ2JWl" / "some_file").touch()
    await state_manager.delete_question("myuQ2JWl")

    question_path = tmp_path / "myuQ2JWl"
    assert not (question_path / FilesystemStateManager.StateFilename.QUESTION_STATE).exists()
    assert question_path.exists()


async def test_read_attempts(state_manager: StateManager) -> None:
    await state_manager.write_question_state("myuQ2JWl", "data1")
    await state_manager.write_question_state("nYKEjBaA", "data2")
    await state_manager.write_question_state("5YfGRyRs", "data3")

    result = await state_manager.read_question_states()

    assert result["myuQ2JWl"] == "data1"
    assert result["nYKEjBaA"] == "data2"
    assert result["5YfGRyRs"] == "data3"
    assert len(result) == 3


async def test_write_read_attempt_state(state_manager: StateManager) -> None:
    test_data = "attempt state data"
    await state_manager.write_attempt_state("myuQ2JWl", "UY9ryXzq", test_data)
    result = await state_manager.read_attempt_state("myuQ2JWl", "UY9ryXzq")

    assert result == test_data


async def test_read_attempt_state_missing_raises(state_manager: StateManager) -> None:
    with pytest.raises(webserver_errors.MissingAttemptStateError):
        await state_manager.read_attempt_state("myuQ2JWl", "UY9ryXzq")


async def test_write_read_attempt_seed(state_manager: StateManager) -> None:
    await state_manager.write_attempt_seed("myuQ2JWl", "UY9ryXzq", 42)
    result = await state_manager.read_attempt_seed("myuQ2JWl", "UY9ryXzq")

    assert result == 42


async def test_read_attempt_seed_missing_raises(state_manager: StateManager) -> None:
    with pytest.raises(webserver_errors.MissingAttemptSeedError):
        await state_manager.read_attempt_seed("myuQ2JWl", "UY9ryXzq")


async def test_write_read_attempt_score(state_manager: StateManager) -> None:
    score = ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=None, score_adjusted=None)
    await state_manager.write_attempt_score("myuQ2JWl", "UY9ryXzq", score)
    result = await state_manager.read_attempt_score("myuQ2JWl", "UY9ryXzq")

    assert result == score


async def test_read_attempt_score_missing_raises(state_manager: StateManager) -> None:
    with pytest.raises(webserver_errors.MissingAttemptScoreError):
        await state_manager.read_attempt_score("myuQ2JWl", "UY9ryXzq")


async def test_write_read_attempt_data(state_manager: StateManager) -> None:
    test_data: dict[str, JsonValue] = {"key": "value", "number": 123}
    await state_manager.write_attempt_data("myuQ2JWl", "UY9ryXzq", test_data)
    result = await state_manager.read_attempt_data("myuQ2JWl", "UY9ryXzq")

    assert result == test_data


async def test_read_attempt_data_missing_raises(state_manager: StateManager) -> None:
    with pytest.raises(webserver_errors.MissingAttemptDataError):
        await state_manager.read_attempt_data("myuQ2JWl", "UY9ryXzq")


async def test_delete_attempt(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_question_state("myuQ2JWl", "question data")
    await state_manager.write_attempt_state("myuQ2JWl", "UY9ryXzq", "attempt data")
    await state_manager.write_attempt_seed("myuQ2JWl", "UY9ryXzq", 123)
    await state_manager.write_attempt_score(
        "myuQ2JWl",
        "UY9ryXzq",
        ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=None, score_adjusted=None),
    )
    await state_manager.delete_attempt("myuQ2JWl", "UY9ryXzq")

    assert not (tmp_path / "myuQ2JWl" / "UY9ryXzq").exists()
    assert (tmp_path / "myuQ2JWl" / FilesystemStateManager.StateFilename.QUESTION_STATE).exists()


async def test_delete_attempt_leaves_other_files(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_attempt_seed("myuQ2JWl", "UY9ryXzq", 123)
    some_file_path = tmp_path / "myuQ2JWl" / "UY9ryXzq" / "some_file"
    some_file_path.touch()
    await state_manager.delete_attempt("myuQ2JWl", "UY9ryXzq")

    assert not (tmp_path / "myuQ2JWl" / "UY9ryXzq" / FilesystemStateManager.StateFilename.ATTEMPT_SEED).exists()
    assert some_file_path.exists()
