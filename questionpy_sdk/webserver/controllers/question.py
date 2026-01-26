#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import hashlib
import tempfile
from collections.abc import AsyncIterable, Mapping
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, BinaryIO, cast

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy.form import OptionsFile, RichTextEditor
from questionpy_common.api.qtype import InvalidQuestionStateError
from questionpy_common.elements import OptionsFormDefinition
from questionpy_sdk.webserver.constants import DEFAULT_REQUEST_INFO
from questionpy_sdk.webserver.controllers.base import BaseController

type OptionsFormBaseValue = str | int | float | bool | list[str] | list[OptionsFile] | RichTextEditor | None
"""Union of supported form value types (w/o nested)."""

type OptionsFormModelValue = Mapping[str, OptionsFormValue]
"""Form value type for elements that support nested `FormModel`, like `group`, `section`, etc."""

type OptionsFormValue = OptionsFormBaseValue | OptionsFormModelValue | list[OptionsFormModelValue]
"""Union of all form value types."""

type OptionsFormData = Mapping[str, OptionsFormValue]
"""Root form data type."""


@dataclass(config=ConfigDict(use_attribute_docstrings=True))
class OptionsStateResponse:
    """Represents the API response data for the question's options state."""

    data: OptionsFormData
    """The question's options form data."""

    is_new: bool
    """Whether the question is newly created and has not been persisted yet."""


class QuestionController(BaseController):
    async def get_form_definition(self, question_id: str) -> OptionsFormDefinition:
        try:
            state = await self._state_manager.read_question_state(question_id)
        except webserver_errors.MissingQuestionStateError:
            state = None

        async with self.get_worker() as worker:
            form_definition, _ = await worker.get_options_form(DEFAULT_REQUEST_INFO, state)

        return form_definition

    async def get_questions(self) -> dict[str, OptionsFormData | webserver_errors.DetailedServerError]:
        states_str = await self._state_manager.read_question_states()
        states: dict[str, OptionsFormData | webserver_errors.DetailedServerError] = {}

        if len(states_str) > 0:
            async with self.get_worker() as worker:
                for question_id in states_str:
                    state = states_str[question_id]
                    try:
                        _, form_data = await worker.get_options_form(DEFAULT_REQUEST_INFO, state)
                    except InvalidQuestionStateError as err:
                        states[question_id] = webserver_errors.DetailedServerError(
                            type(err).__name__, webserver_errors.format_error(err)
                        )
                    else:
                        states[question_id] = cast("OptionsFormData", form_data)

        return states

    async def get_options_state(self, question_id: str) -> OptionsStateResponse:
        try:
            state = await self._state_manager.read_question_state(question_id)
            is_new = False
        except webserver_errors.MissingQuestionStateError:
            state = None
            is_new = True

        async with self.get_worker() as worker:
            _, form_data = await worker.get_options_form(DEFAULT_REQUEST_INFO, state)

        return OptionsStateResponse(data=cast("OptionsFormData", form_data), is_new=is_new)

    async def save_options_state(self, question_id: str, data: dict[str, object]) -> None:
        try:
            old_state = await self._state_manager.read_question_state(question_id)
        except webserver_errors.MissingQuestionStateError:
            old_state = None

        async with self.get_worker() as worker:
            question = await worker.create_question_from_options(
                DEFAULT_REQUEST_INFO, old_state, form_data=data, lms_permissions=None
            )

        await self._state_manager.write_question_state(question_id, question.question_state)

    async def delete_question(self, question_id: str) -> None:
        await self._state_manager.delete_question(question_id)

    async def delete_all_questions(self) -> None:
        await self._state_manager.delete_all_questions()

    async def clone_question(self, question_id: str, new_question_id: str) -> None:
        # Ensure we're not overwriting an existing question
        questions = await self._state_manager.read_question_states()
        if new_question_id in questions:
            raise webserver_errors.DuplicateQuestionError

        state = await self._state_manager.read_question_state(question_id)
        await self._state_manager.write_question_state(new_question_id, state)

    async def add_file(self, filename: str, mime_type: str, reader: AsyncIterable[bytes]) -> OptionsFile:
        # Temp file needed to hash content before saving; reader is single-use.
        # Likely fails on Windows (moving open files)
        with tempfile.NamedTemporaryFile() as tmp_file:
            file_ref, size = await self._process_file(reader, tmp_file)
            await self._state_manager.add_options_file(file_ref, Path(tmp_file.name))

            return OptionsFile(
                path="/",
                filename=filename,
                file_ref=file_ref,
                uploaded_at=datetime.now(UTC),
                mime_type=mime_type,
                size=size,
            )

    async def get_file(
        self, question_id: str, name: str, file_ref: str
    ) -> tuple[OptionsFile, AbstractContextManager[BinaryIO]]:
        return await self._state_manager.get_options_file(question_id, name, file_ref)

    async def _process_file(self, reader: AsyncIterable[bytes], file: IO[bytes]) -> tuple[str, int]:
        sha1_hash = hashlib.sha1()  # noqa: S324
        total_size = 0
        async for chunk in reader:
            sha1_hash.update(chunk)
            total_size += len(chunk)
            file.write(chunk)
        file.flush()
        return sha1_hash.hexdigest(), total_size
