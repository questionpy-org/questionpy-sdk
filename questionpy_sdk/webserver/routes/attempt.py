#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import contextlib

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotFound
from pydantic import RootModel

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy_sdk.webserver.constants import ID_RE
from questionpy_sdk.webserver.controllers.attempt import AttemptController
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


class AttemptBaseView(BaseView["AttemptController"]):
    controller_class = AttemptController


@routes.view(f"/question/{{question_id:{ID_RE}}}/attempt/{{attempt_id:{ID_RE}}}", name="attempt")
class AttemptView(AttemptBaseView):
    async def get(self) -> web.Response:
        """Gets the rendered attempt data."""
        question_id = self.request.match_info["question_id"]
        attempt_id = self.request.match_info["attempt_id"]

        display_options_kwargs: dict[str, str | list[str]] = dict(self.request.query)
        with contextlib.suppress(KeyError):
            display_options_kwargs["roles"] = self.request.query.getall("roles")
        display_options = QuestionDisplayOptions(**display_options_kwargs)

        try:
            data = await self.controller.get_attempt(question_id, attempt_id, display_options)
        except webserver_errors.MissingQuestionStateError as err:
            raise web.HTTPBadRequest(text=str(err)) from err

        return self.json_model_response(RootModel(data))

    async def post(self) -> web.Response:
        """Saves the attempt form data."""
        question_id = self.request.match_info["question_id"]
        attempt_id = self.request.match_info["attempt_id"]

        data = await self.request.json()
        await self.controller.save_attempt(question_id, attempt_id, data)
        return web.Response()

    async def delete(self) -> web.Response:
        """Deletes the attempt from the state storage."""
        question_id = self.request.match_info["question_id"]
        attempt_id = self.request.match_info["attempt_id"]

        try:
            await self.controller.delete_attempt(question_id, attempt_id)
        except webserver_errors.MissingAttemptStateError as err:
            raise HTTPNotFound from err

        return web.json_response()


@routes.view(f"/question/{{question_id:{ID_RE}}}/attempts", name="attempt.list")
class AttemptListView(AttemptBaseView):
    async def get(self) -> web.Response:
        """Gets a list of all saved attempts for the current question."""
        question_id = self.request.match_info["question_id"]
        attempts = await self.controller.get_attempts(question_id)
        return self.json_model_response(RootModel(attempts))


@routes.view(f"/question/{{question_id:{ID_RE}}}/attempt/{{attempt_id:{ID_RE}}}/score", name="attempt.score")
class AttemptScoreView(AttemptBaseView):
    async def post(self) -> web.Response:
        """Scores the saved attempt."""
        question_id = self.request.match_info["question_id"]
        attempt_id = self.request.match_info["attempt_id"]

        try:
            await self.controller.score_attempt(question_id, attempt_id)
        except (
            webserver_errors.MissingQuestionStateError,
            webserver_errors.MissingAttemptStateError,
            webserver_errors.MissingAttemptDataError,
        ) as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        return web.Response()
