#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import contextlib

from aiohttp import web
from pydantic import RootModel

from questionpy_sdk.webserver.controllers.attempt import AttemptController
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions
from questionpy_sdk.webserver.controllers.errors import (
    MissingAttemptDataError,
    MissingAttemptStateError,
    MissingQuestionStateError,
)
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


class AttemptBaseView(BaseView["AttemptController"]):
    controller_class = AttemptController


@routes.view("/attempt")
class AttemptView(AttemptBaseView):
    async def get(self) -> web.Response:
        """Gets the attempt data."""
        display_options_kwargs: dict[str, str | list[str]] = dict(self.request.query)
        with contextlib.suppress(KeyError):
            display_options_kwargs["roles"] = self.request.query.getall("roles")
        display_options = QuestionDisplayOptions(**display_options_kwargs)

        try:
            data = await self.controller.get_attempt(display_options)
        except MissingQuestionStateError as err:
            raise web.HTTPBadRequest(text=str(err)) from err

        return self.json_model_response(RootModel(data))

    async def post(self) -> web.Response:
        """Saves the attempt form data."""
        data = await self.request.json()
        await self.controller.save_attempt(data)
        return web.Response()


@routes.view("/attempt/score")
class AttemptScoreView(AttemptBaseView):
    async def post(self) -> web.Response:
        """Scores the saved attempt."""
        try:
            await self.controller.score_attempt()
        except (MissingQuestionStateError, MissingAttemptStateError, MissingAttemptDataError) as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        return web.Response()


@routes.view("/attempt/restart")
class AttemptResetView(AttemptBaseView):
    async def post(self) -> web.Response:
        """Restarts the attempt by deleting the attempt scored state and last attempt data and by resetting the seed."""
        await self.controller.reset_attempt()
        return web.Response()
