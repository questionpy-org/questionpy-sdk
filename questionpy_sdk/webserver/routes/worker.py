#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING

from aiohttp import web

from questionpy_sdk.webserver.app import SDK_WEBSERVER_APP_KEY

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

routes = web.RouteTableDef()


@routes.get("/worker/{namespace}/{short_name}/file/{path:(static|static-private)/.*}")
async def get_static_file(request: web.Request) -> web.Response:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    namespace = request.match_info["namespace"]
    short_name = request.match_info["short_name"]
    path = request.match_info["path"]

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        if manifest.namespace != namespace or manifest.short_name != short_name:
            return web.HTTPNotFound(reason="Package not found.")

        try:
            file = await worker.get_static_file(path)
        except FileNotFoundError:
            return web.HTTPNotFound(reason="File not found.")

    return web.Response(body=file.data, content_type=file.mime_type, headers={"Cache-Control": "no-cache"})
