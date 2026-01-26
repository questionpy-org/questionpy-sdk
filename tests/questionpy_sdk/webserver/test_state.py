#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import ScoreModel, ScoringCode
from questionpy_sdk.webserver.state import FilesystemStateManager, StateManager

if TYPE_CHECKING:
    from pydantic import JsonValue


@pytest.fixture
def state_manager(tmp_path: Path) -> StateManager:
    return FilesystemStateManager(tmp_path, "test-test-1.00.0")


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

    assert not (tmp_path / "test-test-1.00.0" / "myuQ2JWl").exists()


async def test_delete_all_questions(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_question_state("myuQ2JWl", "data1")
    await state_manager.write_attempt_state("myuQ2JWl", "UY9ryXzq", "attempt data")
    await state_manager.write_question_state("nYKEjBaA", "data2")
    await state_manager.write_question_state("5YfGRyRs", "data3")

    await state_manager.delete_all_questions()

    assert not (tmp_path / "test-test-1.00.0" / "myuQ2JWl").exists()
    assert not (tmp_path / "test-test-1.00.0" / "nYKEjBaA").exists()
    assert not (tmp_path / "test-test-1.00.0" / "5YfGRyRs").exists()


async def test_delete_question_leaves_other_files(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_question_state("myuQ2JWl", "data")
    (tmp_path / "test-test-1.00.0" / "myuQ2JWl" / "some_file").touch()
    await state_manager.delete_question("myuQ2JWl")

    question_path = tmp_path / "test-test-1.00.0" / "myuQ2JWl"
    assert not (question_path / FilesystemStateManager.StateFilename.QUESTION_STATE).exists()
    assert question_path.exists()


async def test_add_options_file(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "abcdef1234567890abcdef1234567890abcdef12"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("test content")

    await state_manager.add_options_file(file_ref, source_file)

    expected_path = tmp_path / "options_files" / "ab" / file_ref
    assert expected_path.exists()
    assert expected_path.read_text() == "test content"
    assert not source_file.exists()


async def test_add_options_file_existing_target(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "abcdef1234567890abcdef1234567890abcdef12"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("test content")

    # Create the target file with the same content (same hash)
    target_path = tmp_path / "options_files" / "ab" / file_ref
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("test content")
    original_mtime = target_path.stat().st_mtime

    await state_manager.add_options_file(file_ref, source_file)

    assert target_path.exists()
    assert target_path.read_text() == "test content"

    # Check that the source file still exists (was not moved); target was not overwritten
    assert source_file.exists()
    assert target_path.stat().st_mtime == original_mtime


async def test_get_options_file(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "abcdef1234567890abcdef1234567890abcdef12"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("test content")

    await state_manager.add_options_file(file_ref, source_file)

    question_state = {
        "options": {
            "file_upload": [
                {
                    "path": "/",
                    "filename": "test_file.txt",
                    "file_ref": file_ref,
                    "uploaded_at": "2025-11-06T15:13:15.631214Z",
                    "mime_type": "text/plain",
                    "size": 12,
                }
            ]
        }
    }

    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))
    options_file, file_context = await state_manager.get_options_file("myuQ2JWl", "file_upload.0", file_ref)

    assert options_file.filename == "test_file.txt"
    assert options_file.file_ref == file_ref
    assert options_file.mime_type == "text/plain"

    with file_context as f:
        content = f.read()
        assert content == b"test content"


async def test_get_options_file_inside_section(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "1234567890abcdef1234567890abcdef12345678"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("inside section")

    await state_manager.add_options_file(file_ref, source_file)

    question_state = {
        "options": {
            "foo_section": {
                "foo_file_upload": [
                    {
                        "path": "/",
                        "filename": "section_file.txt",
                        "file_ref": file_ref,
                        "uploaded_at": "2025-11-06T15:13:28.997740Z",
                        "mime_type": "text/plain",
                        "size": 14,
                    }
                ]
            }
        }
    }

    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))
    options_file, file_context = await state_manager.get_options_file(
        "myuQ2JWl", "foo_section.foo_file_upload.0", file_ref
    )

    assert options_file.filename == "section_file.txt"
    assert options_file.file_ref == file_ref
    assert options_file.mime_type == "text/plain"

    with file_context as f:
        content = f.read()
        assert content == b"inside section"


async def test_get_options_file_inside_group(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "fedcba0987654321fedcba0987654321fedcba09"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("inside group")

    await state_manager.add_options_file(file_ref, source_file)

    question_state = {
        "options": {
            "bar_group": {
                "some_input": "",
                "bar_file_upload": [
                    {
                        "path": "/",
                        "filename": "group_file.txt",
                        "file_ref": file_ref,
                        "uploaded_at": "2025-11-06T15:13:25.082918Z",
                        "mime_type": "text/plain",
                        "size": 12,
                    }
                ],
            }
        }
    }

    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))
    options_file, file_context = await state_manager.get_options_file(
        "myuQ2JWl", "bar_group.bar_file_upload.0", file_ref
    )

    assert options_file.filename == "group_file.txt"
    assert options_file.file_ref == file_ref
    assert options_file.mime_type == "text/plain"

    with file_context as f:
        content = f.read()
        assert content == b"inside group"


async def test_get_options_file_inside_repetition(state_manager: FilesystemStateManager, tmp_path: Path) -> None:
    file_ref = "0123456789abcdef0123456789abcdef01234567"
    source_file = tmp_path / "source_file.txt"
    source_file.write_text("inside repetition")

    await state_manager.add_options_file(file_ref, source_file)

    question_state = {
        "options": {
            "my_repetition": [
                {"some_input": "", "bar_file_upload": []},
                {
                    "some_input": "",
                    "bar_file_upload": [
                        {
                            "path": "/",
                            "filename": "repetition_file.txt",
                            "file_ref": file_ref,
                            "uploaded_at": "2025-11-06T15:13:22.512159Z",
                            "mime_type": "text/plain",
                            "size": 17,
                        }
                    ],
                },
            ]
        }
    }

    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))
    options_file, file_context = await state_manager.get_options_file(
        "myuQ2JWl", "my_repetition.1.bar_file_upload.0", file_ref
    )

    assert options_file.filename == "repetition_file.txt"
    assert options_file.file_ref == file_ref
    assert options_file.mime_type == "text/plain"

    with file_context as f:
        content = f.read()
        assert content == b"inside repetition"


@pytest.mark.parametrize(
    "path",
    [
        "file_upload.0",
        "foo_section.foo_file_upload.0",
        "bar_group.bar_file_upload.0",
        "my_repetition.1.bar_file_upload.0",
    ],
)
async def test_get_options_file_missing_question(state_manager: FilesystemStateManager, path: str) -> None:
    with pytest.raises(webserver_errors.MissingQuestionStateError):
        await state_manager.get_options_file("nonexistent_question", path, "abcdef1234567890abcdef1234567890abcdef12")


def make_question_state(file_ref: str) -> dict[str, Any]:
    return {
        "options": {
            "file_upload": [
                {
                    "path": "/",
                    "filename": "file.txt",
                    "file_ref": file_ref,
                    "uploaded_at": "2025-11-06T15:13:15.631214Z",
                    "mime_type": "text/plain",
                    "size": 4,
                }
            ],
            "foo_section": {
                "foo_file_upload": [
                    {
                        "path": "/",
                        "filename": "file.txt",
                        "file_ref": file_ref,
                        "uploaded_at": "2025-11-06T15:13:28.997740Z",
                        "mime_type": "text/plain",
                        "size": 4,
                    }
                ]
            },
            "bar_group": {
                "some_input": "",
                "bar_file_upload": [
                    {
                        "path": "/",
                        "filename": "file.txt",
                        "file_ref": file_ref,
                        "uploaded_at": "2025-11-06T15:13:25.082918Z",
                        "mime_type": "text/plain",
                        "size": 4,
                    }
                ],
            },
            "my_repetition": [
                {"some_input": ""},
                {
                    "some_input": "",
                    "bar_file_upload": [
                        {
                            "path": "/",
                            "filename": "file.txt",
                            "file_ref": file_ref,
                            "uploaded_at": "2025-11-06T15:13:22.512159Z",
                            "mime_type": "text/plain",
                            "size": 4,
                        }
                    ],
                },
            ],
        }
    }


@pytest.mark.parametrize(
    "path",
    [
        "file_upload.0",
        "foo_section.foo_file_upload.0",
        "bar_group.bar_file_upload.0",
        "my_repetition.1.bar_file_upload.0",
    ],
)
async def test_get_options_file_missing_file(state_manager: FilesystemStateManager, path: str) -> None:
    question_state = make_question_state("different_file_ref")
    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))

    with pytest.raises(webserver_errors.MissingOptionsFileError):
        await state_manager.get_options_file("myuQ2JWl", path, "abcdef1234567890abcdef1234567890abcdef12")


@pytest.mark.parametrize(
    "path",
    [
        "file_upload.0",
        "foo_section.foo_file_upload.0",
        "bar_group.bar_file_upload.0",
        "my_repetition.1.bar_file_upload.0",
    ],
)
async def test_get_options_file_missing_content(state_manager: FilesystemStateManager, path: str) -> None:
    file_ref = "abcdef1234567890abcdef1234567890abcdef12"
    question_state = make_question_state(file_ref)
    await state_manager.write_question_state("myuQ2JWl", json.dumps(question_state))

    _, file_context = await state_manager.get_options_file("myuQ2JWl", path, file_ref)
    with pytest.raises(webserver_errors.MissingOptionsFileError), file_context:
        pass


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

    assert not (tmp_path / "test-test-1.00.0" / "myuQ2JWl" / "UY9ryXzq").exists()
    assert (tmp_path / "test-test-1.00.0" / "myuQ2JWl" / FilesystemStateManager.StateFilename.QUESTION_STATE).exists()


async def test_delete_attempt_leaves_other_files(state_manager: StateManager, tmp_path: Path) -> None:
    await state_manager.write_attempt_seed("myuQ2JWl", "UY9ryXzq", 123)
    some_file_path = tmp_path / "test-test-1.00.0" / "myuQ2JWl" / "UY9ryXzq" / "some_file"
    some_file_path.touch()
    await state_manager.delete_attempt("myuQ2JWl", "UY9ryXzq")

    assert not (
        tmp_path / "test-test-1.00.0" / "myuQ2JWl" / "UY9ryXzq" / FilesystemStateManager.StateFilename.ATTEMPT_SEED
    ).exists()
    assert some_file_path.exists()
