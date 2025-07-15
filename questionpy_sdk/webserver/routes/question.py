#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotFound, HTTPUnprocessableEntity
from pydantic import RootModel

from questionpy import OptionsFormValidationError
from questionpy_sdk.webserver.constants import ID_RE
from questionpy_sdk.webserver.controllers.question import QuestionController
from questionpy_sdk.webserver.errors import MissingQuestionStateError
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


class QuestionBaseView(BaseView["QuestionController"]):
    controller_class = QuestionController


@routes.view(f"/question/{{question_id:{ID_RE}}}", name="question")
class QuestionView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets the options form definition that allows a question creator to customize a question."""
        question_id = self.request.match_info["question_id"]
        return self.json_model_response(await self.controller.get_form_definition(question_id))

    async def delete(self) -> web.Response:
        """Deletes the question and its attempts from the state storage."""
        question_id = self.request.match_info["question_id"]

        try:
            await self.controller.delete_question(question_id)
        except MissingQuestionStateError as err:
            raise HTTPNotFound from err

        return web.json_response()


@routes.view("/questions", name="question.list")
class QuestionListView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets a list of all saved questions for the current package."""
        return web.json_response(await self.controller.get_questions())


@routes.view(f"/question/{{question_id:{ID_RE}}}/state", name="question.state")
class QuestionStateView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets the form data for the Options Form from the state storage."""
        question_id = self.request.match_info["question_id"]
        return self.json_model_response(RootModel(await self.controller.get_options_state(question_id)))

    async def post(self) -> web.Response:
        """Stores the form data from the Options Form in the state storage."""
        question_id = self.request.match_info["question_id"]
        form_data = await self.request.json()

        try:
            await self.controller.save_options_state(question_id, form_data)
        except OptionsFormValidationError as err:
            return web.json_response(err.errors, status=HTTPUnprocessableEntity.status_code)

        return web.json_response()
