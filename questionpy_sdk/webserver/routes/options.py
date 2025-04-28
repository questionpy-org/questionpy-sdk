#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web
from aiohttp.web_exceptions import HTTPUnprocessableEntity

from questionpy import OptionsFormValidationError
from questionpy_sdk.webserver.controllers.options import OptionsController
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


class OptionsBaseView(BaseView["OptionsController"]):
    controller_class = OptionsController


@routes.view("/options")
class OptionsView(OptionsBaseView):
    async def get(self) -> web.Response:
        """Gets the options form definition that allows a question creator to customize a question."""
        return self.json_model_response(await self.controller.get_form_definition())


@routes.view("/options/state")
class OptionsStateView(OptionsBaseView):
    async def get(self) -> web.Response:
        """Gets the form data for the Options Form from the state storage."""
        return web.json_response(await self.controller.get_options_state())

    async def post(self) -> web.Response:
        """Stores the form data from the Options Form in the state storage."""
        form_data = await self.request.json()

        try:
            await self.controller.save_options_state(form_data)
        except OptionsFormValidationError as err:
            return web.json_response(err.errors, status=HTTPUnprocessableEntity.status_code)

        return web.json_response()
