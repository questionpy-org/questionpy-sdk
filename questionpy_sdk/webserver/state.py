#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import json
from enum import StrEnum
from pathlib import Path

from pydantic import JsonValue, TypeAdapter

from questionpy import ScoreModel


class StateFilename(StrEnum):
    QUESTION_STATE = "question_state.txt"
    ATTEMPT_STATE = "attempt_state.txt"
    ATTEMPT_SEED = "attempt_seed.txt"
    SCORE = "score.json"
    LAST_ATTEMPT_DATA = "last_attempt_data.json"


class StateManager:
    """Manages asynchronous reading, writing, and deletion of question package state files.

    This class handles the persistence of various states (e.g., question state, attempt data, scores)
    in a specified directory. All file operations are non-blocking and executed in a thread pool.

    Args:
        package_state_dir: Directory where state files will be stored.
    """

    def __init__(self, package_state_dir: Path) -> None:
        self._package_state_dir = package_state_dir

    async def read_question_state(self) -> str:
        return await self._read_state_file(StateFilename.QUESTION_STATE)

    async def write_question_state(self, question_state: str) -> None:
        await self._write_state_file(StateFilename.QUESTION_STATE, question_state)

    async def read_attempt_state(self) -> str:
        return await self._read_state_file(StateFilename.ATTEMPT_STATE)

    async def write_attempt_state(self, attempt_state: str) -> None:
        await self._write_state_file(StateFilename.ATTEMPT_STATE, attempt_state)

    async def read_attempt_seed(self) -> int:
        return int(await self._read_state_file(StateFilename.ATTEMPT_SEED))

    async def write_attempt_seed(self, seed: int) -> None:
        await self._write_state_file(StateFilename.ATTEMPT_SEED, str(seed))

    async def read_score(self) -> ScoreModel:
        score_json = await self._read_state_file(StateFilename.SCORE)
        return ScoreModel.model_validate_json(score_json)

    async def write_score(self, score: ScoreModel) -> None:
        score_json = TypeAdapter(ScoreModel).dump_json(score).decode()
        await self._write_state_file(StateFilename.SCORE, score_json)

    async def read_last_attempt_data(self) -> dict[str, JsonValue]:
        last_attempt_data_json = await self._read_state_file(StateFilename.LAST_ATTEMPT_DATA)
        return json.loads(last_attempt_data_json)

    async def write_last_attempt_data(self, data: dict[str, JsonValue]) -> None:
        await self._write_state_file(StateFilename.LAST_ATTEMPT_DATA, json.dumps(data))

    async def delete_state(self) -> None:
        def _cleanup() -> None:
            for fname in (
                StateFilename.ATTEMPT_STATE,
                StateFilename.SCORE,
                StateFilename.LAST_ATTEMPT_DATA,
                StateFilename.ATTEMPT_SEED,
            ):
                self._filepath(fname).unlink(missing_ok=True)
            if not any(self._package_state_dir.iterdir()):
                self._package_state_dir.rmdir()

        await asyncio.to_thread(_cleanup)

    async def _read_state_file(self, filename: StateFilename) -> str:
        return await asyncio.to_thread(self._filepath(filename).read_text)

    async def _write_state_file(self, filename: StateFilename, data: str) -> None:
        await asyncio.to_thread(self._package_state_dir.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(self._filepath(filename).write_text, data)

    def _filepath(self, filename: str) -> Path:
        return self._package_state_dir / filename
