#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy_common.api.qtype import InvalidQuestionStateError
from questionpy_common.elements import OptionsFormDefinition
from questionpy_sdk.webserver.constants import DEFAULT_REQUEST_INFO
from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_sdk.webserver.controllers.question._form_data import OptionsFormData, flatten_form_data, parse_form_data


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
                        form_definition, form_data = await worker.get_options_form(DEFAULT_REQUEST_INFO, state)
                    except InvalidQuestionStateError as err:
                        states[question_id] = webserver_errors.DetailedServerError(
                            type(err).__name__, webserver_errors.format_error(err)
                        )
                    else:
                        section_names = self._section_names_from_definition(form_definition)
                        flat_form_data = flatten_form_data(form_data, section_names)
                        states[question_id] = flat_form_data

        return states

    async def get_options_state(self, question_id: str) -> OptionsStateResponse:
        try:
            state = await self._state_manager.read_question_state(question_id)
            is_new = False
        except webserver_errors.MissingQuestionStateError:
            state = None
            is_new = True

        async with self.get_worker() as worker:
            form_definition, form_data = await worker.get_options_form(DEFAULT_REQUEST_INFO, state)

        return OptionsStateResponse(
            data=flatten_form_data(form_data, self._section_names_from_definition(form_definition)),
            is_new=is_new,
        )

    async def save_options_state(self, question_id: str, data: OptionsFormData) -> None:
        form_data = parse_form_data(data)

        try:
            old_state = await self._state_manager.read_question_state(question_id)
        except webserver_errors.MissingQuestionStateError:
            old_state = None

        async with self.get_worker() as worker:
            question = await worker.create_question_from_options(
                DEFAULT_REQUEST_INFO, old_state, form_data=form_data, lms_permissions=None
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

    @staticmethod
    def _section_names_from_definition(form_definition: OptionsFormDefinition) -> list[str]:
        return [section.name for section in form_definition.sections]
