#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from questionpy import ScoreModel, ScoringCode
from questionpy_sdk.webserver.state import StateFilename, StateManager

if TYPE_CHECKING:
    from pydantic import JsonValue


async def test_write_read_question_state(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    test_data = "question state data"
    await sm.write_question_state(test_data)
    result = await sm.read_question_state()
    assert result == test_data


async def test_write_read_attempt_state(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    test_data = "attempt state data"
    await sm.write_attempt_state(test_data)
    result = await sm.read_attempt_state()
    assert result == test_data


async def test_write_read_attempt_seed(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    test_seed = 42
    await sm.write_attempt_seed(test_seed)
    result = await sm.read_attempt_seed()
    assert result == test_seed


async def test_write_read_score(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    original_score = ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=None, score_final=None)
    await sm.write_score(original_score)
    read_score = await sm.read_score()
    assert read_score == original_score


async def test_write_read_last_attempt_data(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    test_data: dict[str, JsonValue] = {"key": "value", "number": 123}
    await sm.write_last_attempt_data(test_data)
    result = await sm.read_last_attempt_data()
    assert result == test_data


async def test_delete_state_removes_files(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    await sm.write_attempt_state("attempt")
    await sm.write_attempt_seed(123)
    await sm.write_score(ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=None, score_final=None))
    await sm.write_question_state("question")

    await sm.delete_state()

    assert not (tmp_path / StateFilename.ATTEMPT_STATE).exists()
    assert not (tmp_path / StateFilename.ATTEMPT_SEED).exists()
    assert not (tmp_path / StateFilename.SCORE).exists()
    assert not (tmp_path / StateFilename.LAST_ATTEMPT_DATA).exists()
    assert (tmp_path / StateFilename.QUESTION_STATE).exists()
    assert tmp_path.exists()


async def test_delete_state_removes_directory_if_empty(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    await sm.write_attempt_state("data")
    await sm.delete_state()
    assert not tmp_path.exists()


async def test_delete_state_leaves_other_files(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    other_file = tmp_path / "other.txt"
    other_file.write_text("content")
    await sm.write_attempt_seed(123)

    await sm.delete_state()

    assert not (tmp_path / StateFilename.ATTEMPT_SEED).exists()
    assert other_file.exists()
    assert tmp_path.exists()


async def test_read_missing_file_raises(tmp_path: Path) -> None:
    sm = StateManager(tmp_path)
    with pytest.raises(FileNotFoundError):
        await sm.read_question_state()


async def test_write_creates_directory(tmp_path: Path) -> None:
    package_dir = tmp_path / "state_dir"
    sm = StateManager(package_dir)
    assert not package_dir.exists()
    await sm.write_question_state("data")
    assert package_dir.exists()
