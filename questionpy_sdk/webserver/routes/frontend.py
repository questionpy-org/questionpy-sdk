#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from aiohttp import web

from questionpy_sdk.webserver.constants import STATIC_DIR

routes = web.RouteTableDef()


@routes.get("/{path:.*}")
async def serve_frontend(request: web.Request) -> web.StreamResponse:
    path = request.match_info.get("path", "")

    # Prevent directory traversal
    try:
        file_path = (STATIC_DIR / path).resolve()
        # Ensure the resolved path is within the static directory
        if not file_path.is_relative_to(STATIC_DIR.resolve()):
            raise web.HTTPNotFound
    except (ValueError, FileNotFoundError) as err:
        raise web.HTTPNotFound from err

    if file_path.is_file():
        return web.FileResponse(file_path)

    # Serve index.html for all other paths
    return web.FileResponse(STATIC_DIR / "index.html")
