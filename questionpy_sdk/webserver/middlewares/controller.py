#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from inspect import isclass

from aiohttp import web
from aiohttp.typedefs import Handler

from questionpy_sdk.webserver.constants import REQUEST_CONTROLLER_KEY, WEBSERVER_KEY
from questionpy_sdk.webserver.routes.base import BaseView


@web.middleware
async def inject_controller_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Injects a controller instance to the request object."""
    # Get the raw view class from the route table
    route = request.match_info.route
    if hasattr(route, "handler"):
        view_class = route.handler
        if isclass(view_class) and issubclass(view_class, BaseView):
            request[REQUEST_CONTROLLER_KEY] = view_class.controller_class(request.app[WEBSERVER_KEY])

    return await handler(request)
