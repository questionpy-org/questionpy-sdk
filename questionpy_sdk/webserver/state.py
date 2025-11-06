#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import json
import re
import shutil
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, suppress
from enum import StrEnum
from pathlib import Path
from typing import Any, BinaryIO, NamedTuple, Protocol

from pydantic import JsonValue, RootModel, TypeAdapter, ValidationError

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import ScoreModel
from questionpy.form import OptionsFile
from questionpy_sdk.webserver.constants import ID_RE

OptionsFiles = RootModel[dict[str, OptionsFile]]
"""A mapping of file_refs to OptionsFiles."""


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
    async def delete_all_questions(self) -> None: ...

    async def add_options_file(self, file_ref: str, filepath: Path) -> None: ...
    async def get_options_file(
        self, question_id: str, name: str, file_ref: str
    ) -> tuple[OptionsFile, AbstractContextManager[BinaryIO]]: ...

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

    OPTIONS_FILES_DIR = "options_files"

    def __init__(self, storage_root: Path, package_state_dir: str) -> None:
        self._storage_root = storage_root
        self._package_state_path = storage_root / package_state_dir

    # ------ Questions

    async def read_question_states(self) -> dict[str, str]:
        def _read_question_states() -> dict[str, str]:
            try:
                return {
                    path.name: (path / self.StateFilename.QUESTION_STATE).read_text()
                    for path in self._get_question_state_paths()
                }
            except FileNotFoundError as err:
                raise webserver_errors.MissingQuestionStateError from err

        return await asyncio.to_thread(_read_question_states)

    async def read_question_state(self, question_id: str) -> str:
        try:
            return await self._read_state_file(self._get_question_path(question_id), self.StateFilename.QUESTION_STATE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingQuestionStateError from err

    async def write_question_state(self, question_id: str, question_state: str) -> None:
        path = self._get_question_path(question_id)
        await self._write_state_file(path, self.StateFilename.QUESTION_STATE, question_state)

    async def delete_question(self, question_id: str) -> None:
        await asyncio.to_thread(self._delete_question_sync, question_id)

    def _delete_question_sync(self, question_id: str) -> None:
        question_path = self._get_question_path(question_id)
        try:
            (question_path / self.StateFilename.QUESTION_STATE).unlink()
        except FileNotFoundError as err:
            raise webserver_errors.MissingQuestionStateError from err

        try:
            dir_entries = list(question_path.iterdir())
        except FileNotFoundError:
            return
        for path in dir_entries:
            if self._is_id_dir(path):
                self._delete_attempt_data_sync(question_id, path.name)

        with suppress(OSError):
            # Ignore in case of non-empty directory
            question_path.rmdir()

    async def delete_all_questions(self) -> None:
        def _delete_all_questions() -> None:
            for path in self._get_question_state_paths():
                self._delete_question_sync(path.name)

        await asyncio.to_thread(_delete_all_questions)

    # ------ Options files

    async def add_options_file(self, file_ref: str, filepath: Path) -> None:
        await asyncio.to_thread(self._add_options_file_sync, file_ref, filepath)

    def _add_options_file_sync(self, file_ref: str, filepath: Path) -> None:
        target_path = self._get_sharded_path(file_ref)
        # If the same content exists already, no need to overwrite
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(filepath, target_path)

    async def get_options_file(
        self, question_id: str, name: str, file_ref: str
    ) -> tuple[OptionsFile, AbstractContextManager[BinaryIO]]:
        state = await self.read_question_state(question_id)
        options_file = self._find_file(json.loads(state)["options"], name, file_ref)
        content_path = self._get_sharded_path(file_ref)

        @contextmanager
        def read_bytes() -> Iterator[BinaryIO]:
            try:
                with content_path.open("rb") as f:
                    yield f
            except FileNotFoundError as err:
                raise webserver_errors.MissingOptionsFileError from err

        return options_file, read_bytes()

    @staticmethod
    def _find_file(opts: dict[str, Any], name: str, file_ref: str) -> OptionsFile:
        """Find an `OptionsFile` inside the form data."""

        def get_item(cur: dict[str, Any] | list[Any], p: str | int) -> Any:
            # Makes mypy happy about cur/p types
            if isinstance(p, int):
                if not isinstance(cur, list):
                    msg = f"Expected list for index {p}, got {type(cur).__name__}"
                    raise TypeError(msg)
                return cur[p]
            if not isinstance(cur, dict):
                msg = f"Expected dict for key {p}, got {type(cur).__name__}"
                raise TypeError(msg)
            return cur[p]

        # Parse path
        parts = [int(p) if p.isdigit() else p for p in name.split(".")]
        if parts and parts[0] == "general":
            parts = parts[1:]  # treat `general` as root-level

        cur: dict[str, Any] | list[Any] = opts
        with suppress(KeyError, IndexError, TypeError, StopIteration, ValidationError):
            # Descend into options tree
            for p in parts:
                cur = get_item(cur, p)
            if isinstance(cur, dict) and cur.get("file_ref") == file_ref:
                # File found
                return OptionsFile.model_validate(cur)

        raise webserver_errors.MissingOptionsFileError

    def _get_sharded_path(self, file_ref: str) -> Path:
        """Get sharded file path, e.g. `options_files/ab/abcdef...`."""
        return self._storage_root / self.OPTIONS_FILES_DIR / file_ref[:2] / file_ref

    # ------ Attempts

    async def read_attempts(self, question_id: str) -> dict[str, Attempt]:
        return await asyncio.to_thread(self._read_attempts_sync, question_id)

    def _read_attempts_sync(self, question_id: str) -> dict[str, Attempt]:
        attempts: dict[str, Attempt] = {}

        try:
            dir_entries = list(self._get_question_path(question_id).iterdir())
        except FileNotFoundError:
            # Question dir might not have been created yet
            return attempts

        for path in dir_entries:
            if self._is_id_dir(path):
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
                attempts[path.name] = Attempt(state, seed, score, data)

        return attempts

    async def read_attempt_state(self, question_id: str, attempt_id: str) -> str:
        path = self._get_attempt_path(question_id, attempt_id)
        try:
            return await self._read_state_file(path, self.StateFilename.ATTEMPT_STATE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptStateError from err

    async def write_attempt_state(self, question_id: str, attempt_id: str, attempt_state: str) -> None:
        path = self._get_attempt_path(question_id, attempt_id)
        await self._write_state_file(path, self.StateFilename.ATTEMPT_STATE, attempt_state)

    async def read_attempt_seed(self, question_id: str, attempt_id: str) -> int:
        path = self._get_attempt_path(question_id, attempt_id)
        try:
            seed_str = await self._read_state_file(path, self.StateFilename.ATTEMPT_SEED)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptSeedError from err
        return int(seed_str)

    async def write_attempt_seed(self, question_id: str, attempt_id: str, seed: int) -> None:
        await self._write_state_file(
            self._get_attempt_path(question_id, attempt_id), self.StateFilename.ATTEMPT_SEED, str(seed)
        )

    async def read_attempt_score(self, question_id: str, attempt_id: str) -> ScoreModel:
        path = self._get_attempt_path(question_id, attempt_id)
        try:
            score_json = await self._read_state_file(path, self.StateFilename.ATTEMPT_SCORE)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptScoreError from err
        return ScoreModel.model_validate_json(score_json)

    async def write_attempt_score(self, question_id: str, attempt_id: str, score: ScoreModel) -> None:
        score_json = TypeAdapter(ScoreModel).dump_json(score).decode()
        await self._write_state_file(
            self._get_attempt_path(question_id, attempt_id), self.StateFilename.ATTEMPT_SCORE, score_json
        )

    async def read_attempt_data(self, question_id: str, attempt_id: str) -> dict[str, JsonValue]:
        path = self._get_attempt_path(question_id, attempt_id)
        try:
            attempt_data_json = await self._read_state_file(path, self.StateFilename.ATTEMPT_DATA)
        except FileNotFoundError as err:
            raise webserver_errors.MissingAttemptDataError from err
        return json.loads(attempt_data_json)

    async def write_attempt_data(self, question_id: str, attempt_id: str, data: dict[str, JsonValue]) -> None:
        path = self._get_attempt_path(question_id, attempt_id)
        await self._write_state_file(path, self.StateFilename.ATTEMPT_DATA, json.dumps(data))

    async def delete_attempt(self, question_id: str, attempt_id: str) -> None:
        await asyncio.to_thread(self._delete_attempt_data_sync, question_id, attempt_id)

    def _delete_attempt_data_sync(self, question_id: str, attempt_id: str) -> None:
        attempt_path = self._get_attempt_path(question_id, attempt_id)
        if not attempt_path.exists():
            raise webserver_errors.MissingAttemptStateError
        for fname in (
            self.StateFilename.ATTEMPT_STATE,
            self.StateFilename.ATTEMPT_SCORE,
            self.StateFilename.ATTEMPT_DATA,
            self.StateFilename.ATTEMPT_SEED,
        ):
            (attempt_path / fname).unlink(missing_ok=True)
        with suppress(OSError):
            # Ignore in case of non-empty directory
            attempt_path.rmdir()

    # ------ Helpers

    async def _read_state_file(self, path: Path, filename: "FilesystemStateManager.StateFilename") -> str:
        return await asyncio.to_thread((path / filename).read_text)

    async def _write_state_file(self, path: Path, filename: "FilesystemStateManager.StateFilename", data: str) -> None:
        def _write_state_file() -> None:
            path.mkdir(parents=True, exist_ok=True)
            (path / filename).write_text(data)

        await asyncio.to_thread(_write_state_file)

    def _get_question_path(self, question_id: str) -> Path:
        return self._package_state_path / question_id

    def _get_attempt_path(self, question_id: str, attempt_id: str) -> Path:
        return self._get_question_path(question_id) / attempt_id

    def _get_question_state_paths(self) -> list[Path]:
        try:
            return [p for p in self._package_state_path.iterdir() if self._is_id_dir(p)]
        except FileNotFoundError:
            # Package dir might not have been created yet
            return []

    @staticmethod
    def _is_id_dir(path: Path) -> bool:
        return path.is_dir() and bool(re.match(ID_RE, path.name))
