#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web

from questionpy_sdk.webserver.controllers.manifest import ManifestController
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


@routes.view("/manifest")
class ManifestView(BaseView["ManifestController"]):
    controller_class = ManifestController

    async def get(self) -> web.Response:
        """Gets the manifest data."""
        return self.json_model_response(self.controller.get_manifest())
