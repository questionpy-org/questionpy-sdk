#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import os
from pathlib import Path

from aiohttp import web


def serve_frontend(app: web.Application) -> None:
    # Reverse proxy dev server...
    if os.getenv("USE_VITE_DEV_SERVER") == "true":
        from questionpy_sdk.webserver.dev_middleware import vite_devserver_middleware  # noqa: PLC0415

        app.middlewares.append(vite_devserver_middleware)

    # ...or serve frontend dist build.
    else:
        static_dir = Path(__file__).parent.parent / "static"

        async def handle_spa(request: web.Request) -> web.StreamResponse:
            path = request.match_info.get("path", "")

            # Prevent directory traversal
            try:
                file_path = (static_dir / path).resolve()
                # Ensure the resolved path is within the static directory
                if not file_path.is_relative_to(static_dir.resolve()):
                    raise web.HTTPNotFound
            except (ValueError, FileNotFoundError) as err:
                raise web.HTTPNotFound from err

            if file_path.is_file():
                return web.FileResponse(file_path)

            # Serve index.html for all other paths
            return web.FileResponse(static_dir / "index.html")

        # Catch-all route for all GET requests
        app.router.add_get("/{path:.*}", handle_spa)
