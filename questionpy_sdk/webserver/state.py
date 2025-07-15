#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import contextlib
import json
import re
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple, Protocol

from pydantic import JsonValue, TypeAdapter

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import ScoreModel
from questionpy_sdk.webserver.constants import ID_RE


class Attempt(NamedTuple):
    state: str
    seed: int | None
    score: ScoreModel | None
    data: dict[str, JsonValue] | None


class StateManager(Protocol):
    """Manages package state.

    This protocol defines how question and attempt data are persisted.
    """

    async def read_question_states(self) -> dict[str, str]: ...
    async def read_question_state(self, question_id: str) -> str: ...
    async def write_question_state(self, question_id: str, question_state: str) -> None: ...

    async def delete_question(self, question_id: str) -> None: ...

    async def read_attempts(self, question_id: str) -> dict[str, Attempt]: ...
    async def read_attempt_state(self, question_id: str, attempt_id: str) -> str: ...
    async def write_attempt_state(self, question_id: str, attempt_id: str, attempt_state: str) -> None: ...

    async def read_attempt_seed(self, question_id: str, attempt_id: str) -> int: ...
    async def write_attempt_seed(self, question_id: str, attempt_id: str, seed: int) -> None: ...

    async def read_attempt_score(self, question_id: str, attempt_id: str) -> ScoreModel: ...
    async def write_attempt_score(self, question_id: str, attempt_id: str, score: ScoreModel) -> None: ...

    async def read_attempt_data(self, question_id: str, attempt_id: str) -> dict[str, JsonValue]: ...
    async def write_attempt_data(self, question_id: str, attempt_id: str, data: dict[str, JsonValue]) -> None: ...

    async def delete_attempt(self, question_id: str, attempt_id: str) -> None: ...


class FilesystemStateManager:
    """Handles asynchronous reading, writing, and deletion of question package state files.

    Manages persistence of state within the specified directory. All file operations are non-blocking
    and run in a thread pool.

    Args:
        package_state_dir: Directory where state files are stored.
    """

    class StateFilename(StrEnum):
        QUESTION_STATE = "question_state.txt"
        ATTEMPT_STATE = "attempt_state.txt"
        ATTEMPT_SEED = "attempt_seed.txt"
        ATTEMPT_SCORE = "score.json"
        ATTEMPT_DATA = "attempt_data.json"

    def __init__(self, package_state_dir: Path) -> None:
        self._package_state_dir = package_state_dir

    async def read_question_states(self) -> dict[str, str]:
        def _read_question_states() -> dict[str, str]:
            try:
                dir_iter = self._package_state_dir.iterdir()
            except FileNotFoundError:
                # Package dir might not have been created yet
                return {}
            else:
                return {
                    str(path.name): (path / self.StateFilename.QUESTION_STATE).read_text()
                    for path in dir_iter
                    if path.is_dir() and re.match(ID_RE, str(path.name))
                }

        return await asyncio.to_thread(_read_question_states)

    async def read_question_state(self, question_id: str) -> str:
        try:
            return await self._read_state_file(self._question_path(question_id), self.StateFilename.QUESTION_STATE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingQuestionStateError from err

    async def write_question_state(self, question_id: str, question_state: str) -> None:
        path = self._question_path(question_id)
        await self._write_state_file(path, self.StateFilename.QUESTION_STATE, question_state)

    async def delete_question(self, question_id: str) -> None:
        def _delete_question() -> None:
            question_path = self._question_path(question_id)
            try:
                (question_path / self.StateFilename.QUESTION_STATE).unlink()
            except FileNotFoundError as err:
                raise webserver_errors.MissingQuestionStateError from err
            for path in question_path.iterdir():
                if path.is_dir() and re.match(ID_RE, path.name):
                    self._delete_attempt_data_sync(question_id, path.name)
            with contextlib.suppress(OSError):
                # Ignore in case of non-empty directory
                question_path.rmdir()

        await asyncio.to_thread(_delete_question)

    async def read_attempts(self, question_id: str) -> dict[str, Attempt]:
        return await asyncio.to_thread(self._read_attempts_sync, question_id)

    def _read_attempts_sync(self, question_id: str) -> dict[str, Attempt]:
        attempts: dict[str, Attempt] = {}

        try:
            dir_iter = self._question_path(question_id).iterdir()
        except FileNotFoundError:
            # Question dir might not have been created yet
            return attempts

        for path in dir_iter:
            attempt_id = str(path.name)
            if path.is_dir() and re.match(ID_RE, attempt_id):
                state = (path / self.StateFilename.ATTEMPT_STATE).read_text()
                try:
                    seed = int((path / self.StateFilename.ATTEMPT_SEED).read_text())
                except FileNotFoundError:
                    seed = None
                try:
                    score_json = (path / self.StateFilename.ATTEMPT_SCORE).read_text()
                    score = ScoreModel.model_validate_json(score_json)
                except FileNotFoundError:
                    score = None
                try:
                    data = json.loads((path / self.StateFilename.ATTEMPT_DATA).read_text())
                except FileNotFoundError:
                    data = None
                attempts[attempt_id] = Attempt(state, seed, score, data)

        return attempts

    async def read_attempt_state(self, question_id: str, attempt_id: str) -> str:
        path = self._attempt_path(question_id, attempt_id)
        try:
            return await self._read_state_file(path, self.StateFilename.ATTEMPT_STATE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptStateError from err

    async def write_attempt_state(self, question_id: str, attempt_id: str, attempt_state: str) -> None:
        path = self._attempt_path(question_id, attempt_id)
        await self._write_state_file(path, self.StateFilename.ATTEMPT_STATE, attempt_state)

    async def read_attempt_seed(self, question_id: str, attempt_id: str) -> int:
        path = self._attempt_path(question_id, attempt_id)
        try:
            seed_str = await self._read_state_file(path, self.StateFilename.ATTEMPT_SEED)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptSeedError from err
        return int(seed_str)

    async def write_attempt_seed(self, question_id: str, attempt_id: str, seed: int) -> None:
        await self._write_state_file(
            self._attempt_path(question_id, attempt_id), self.StateFilename.ATTEMPT_SEED, str(seed)
        )

    async def read_attempt_score(self, question_id: str, attempt_id: str) -> ScoreModel:
        path = self._attempt_path(question_id, attempt_id)
        try:
            score_json = await self._read_state_file(path, self.StateFilename.ATTEMPT_SCORE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptScoreError from err
        return ScoreModel.model_validate_json(score_json)

    async def write_attempt_score(self, question_id: str, attempt_id: str, score: ScoreModel) -> None:
        score_json = TypeAdapter(ScoreModel).dump_json(score).decode()
        await self._write_state_file(
            self._attempt_path(question_id, attempt_id), self.StateFilename.ATTEMPT_SCORE, score_json
        )

    async def read_attempt_data(self, question_id: str, attempt_id: str) -> dict[str, JsonValue]:
        path = self._attempt_path(question_id, attempt_id)
        try:
            attempt_data_json = await self._read_state_file(path, self.StateFilename.ATTEMPT_DATA)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptDataError from err
        return json.loads(attempt_data_json)

    async def write_attempt_data(self, question_id: str, attempt_id: str, data: dict[str, JsonValue]) -> None:
        path = self._attempt_path(question_id, attempt_id)
        await self._write_state_file(path, self.StateFilename.ATTEMPT_DATA, json.dumps(data))

    async def delete_attempt(self, question_id: str, attempt_id: str) -> None:
        await asyncio.to_thread(self._delete_attempt_data_sync, question_id, attempt_id)

    def _delete_attempt_data_sync(self, question_id: str, attempt_id: str) -> None:
        attempt_path = self._attempt_path(question_id, attempt_id)
        if not attempt_path.exists():
            raise webserver_errors.MissingAttemptStateError
        for fname in (
            self.StateFilename.ATTEMPT_STATE,
            self.StateFilename.ATTEMPT_SCORE,
            self.StateFilename.ATTEMPT_DATA,
            self.StateFilename.ATTEMPT_SEED,
        ):
            (attempt_path / fname).unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            # Ignore in case of non-empty directory
            attempt_path.rmdir()

    async def _read_state_file(self, path: Path, filename: "FilesystemStateManager.StateFilename") -> str:
        return await asyncio.to_thread((path / filename).read_text)

    async def _write_state_file(self, path: Path, filename: "FilesystemStateManager.StateFilename", data: str) -> None:
        def _write_state_file() -> None:
            path.mkdir(parents=True, exist_ok=True)
            (path / filename).write_text(data)

        await asyncio.to_thread(_write_state_file)

    def _question_path(self, question_id: str) -> Path:
        return self._package_state_dir / question_id

    def _attempt_path(self, question_id: str, attempt_id: str) -> Path:
        return self._question_path(question_id) / attempt_id
