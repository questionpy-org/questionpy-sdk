#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING, Any

from questionpy_sdk.webserver.constants import DEFAULT_REQUEST_USER
from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_sdk.webserver.controllers.options._form_data import flatten_form_data, parse_form_data

if TYPE_CHECKING:
    from questionpy_common.elements import OptionsFormDefinition
    from questionpy_server.worker import Worker


class OptionsController(BaseController):
    async def get_form_definition(self) -> "OptionsFormDefinition":
        state = await self._get_question_state(allow_missing=True)

        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            return (await worker.get_options_form(DEFAULT_REQUEST_USER, state))[0]

    async def get_options_state(self) -> dict[str, Any]:
        state = await self._get_question_state(allow_missing=True)

        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            form_definition, form_data = await worker.get_options_form(DEFAULT_REQUEST_USER, state)

        section_names = [section.name for section in form_definition.sections]
        return flatten_form_data(form_data, section_names)

    async def save_options_state(self, data: dict[str, Any]) -> None:
        form_data = parse_form_data(data)
        old_state = await self._get_question_state(allow_missing=True)

        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            question = await worker.create_question_from_options(DEFAULT_REQUEST_USER, old_state, form_data=form_data)

        await self._state_manager.write_question_state(question.question_state)
