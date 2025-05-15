#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
import logging
import traceback

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_exceptions import HTTPBadRequest, HTTPInternalServerError
from pydantic import ValidationError

log = logging.getLogger("questionpy-sdk:web-server")


def format_error(err: Exception) -> str:
    return "".join(traceback.format_exception(err))


@web.middleware
async def api_error_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Custom error handler for API requests.

    - Formats Pydantic validation errors.
    - Formats HTTP exceptions.
    - Includes Traceback for unexpected errors.
    """
    try:
        return await handler(request)
    except ValidationError as err:
        log.exception("Validation error")
        data = {"error": type(err).__name__, "details": err.errors()}
        raise HTTPBadRequest(text=json.dumps(data), content_type="application/json") from err
    except web.HTTPException as exc:
        # Pass through but return JSON
        exc.content_type = "application/json"
        exc.text = json.dumps({"error": exc.text})
        raise
    except Exception as err:
        log.exception("Server error")
        data = {"error": type(err).__name__, "details": format_error(err)}
        raise HTTPInternalServerError(text=json.dumps(data), content_type="application/json") from err


@web.middleware
async def error_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Error handler that shows the exception traceback in the response and logs it to the console."""
    try:
        return await handler(request)
    except web.HTTPException:
        # Allow HTTPExceptions pass through
        raise
    except Exception as err:
        log.exception("Server error")
        raise HTTPInternalServerError(text=f"Server error:\n{format_error(err)}") from err
