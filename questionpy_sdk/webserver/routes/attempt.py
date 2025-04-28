#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from json import JSONEncoder
from typing import Any

from aiohttp import web

from questionpy_sdk.webserver.controllers.attempt import AttemptController
from questionpy_sdk.webserver.controllers.attempt.errors import RenderError, RenderErrorCollection
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


class AttemptBaseView(BaseView["AttemptController"]):
    controller_class = AttemptController


class CustomJSONEncoder(JSONEncoder):
    """A JSON encoder that can handle render error objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, RenderError):
            return obj.to_json()
        if isinstance(obj, RenderErrorCollection):
            return list(obj)
        return super().default(obj)


@routes.view("/attempt")
class AttemptView(AttemptBaseView):
    async def get(self) -> web.Response:
        """Gets the attempt data."""
        params = self.request.query
        display_options = QuestionDisplayOptions(
            general_feedback=params.get("generalFeedback", "true").lower() == "true",
            specific_feedback=params.get("specificFeedback", "true").lower() == "true",
            right_answer=params.get("rightAnswer", "true").lower() == "true",
            roles=params.getall("roles", []),
        )

        return web.json_response(
            data=await self.controller.get_attempt(display_options),
            dumps=lambda obj: json.dumps(obj, cls=CustomJSONEncoder),
        )

    async def post(self) -> web.Response:
        """Saves the attempt form data."""
        data = await self.request.json()
        await self.controller.save_attempt(data)
        return web.Response()


@routes.view("/attempt/score")
class AttemptScoreView(AttemptBaseView):
    async def post(self) -> web.Response:
        """Scores the saved attempt."""
        await self.controller.score_attempt()
        return web.Response()


@routes.view("/attempt/restart")
class AttemptResetView(AttemptBaseView):
    async def post(self) -> web.Response:
        """Restarts the attempt by deleting the attempt scored state and last attempt data and by resetting the seed."""
        await self.controller.reset_attempt()
        return web.Response()
