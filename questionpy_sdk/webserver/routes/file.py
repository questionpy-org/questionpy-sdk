#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotImplemented

from questionpy_sdk.webserver.controllers.file import FileController
from questionpy_sdk.webserver.routes.base import BaseView

routes = web.RouteTableDef()


@routes.view(r"/file/{namespace}/{short_name}/{path:(static|static-private)/.*}", name="file")
class FileView(BaseView["FileController"]):
    controller_class = FileController

    async def get(self) -> web.Response:
        """Gets the file from the specified package at the given path."""
        namespace = self.request.match_info["namespace"]
        short_name = self.request.match_info["short_name"]
        path = self.request.match_info["path"]

        try:
            file = await self.controller.get_static_file(namespace, short_name, path)
        except FileNotFoundError as e:
            raise web.HTTPNotFound(text="File not found.") from e
        except ValueError as e:
            raise HTTPNotImplemented(text=str(e)) from e

        return web.Response(
            body=file.data,
            content_type=file.mime_type,
            headers={"Cache-Control": "no-store"},
        )
