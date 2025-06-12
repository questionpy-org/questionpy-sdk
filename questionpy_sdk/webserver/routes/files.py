#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotImplemented

from questionpy_sdk.webserver.controllers.files import FilesController
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


@routes.view(r"/file/{namespace}/{short_name}/{path:static/.*}")
class FilesView(BaseView["FilesController"]):
    controller_class = FilesController

    async def get(self) -> web.Response:
        """Gets the file from the specified package at the given path."""
        namespace = self.request.match_info["namespace"]
        short_name = self.request.match_info["short_name"]
        path = self.request.match_info["path"]

        manifest = self.controller.get_manifest()
        if manifest.namespace != namespace or manifest.short_name != short_name:
            # TODO: Support static files in non-main packages by using namespace and short_name.
            raise HTTPNotImplemented(text="Static file retrieval from non-main packages is not supported yet.")

        try:
            file = await self.controller.get_static_file(path)
        except FileNotFoundError as e:
            raise web.HTTPNotFound(text="File not found.") from e

        return web.Response(
            body=file.data,
            content_type=file.mime_type,
            headers={"Cache-Control": "no-store"},
        )
