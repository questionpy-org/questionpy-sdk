#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_exceptions import HTTPBadRequest, HTTPInternalServerError
from pydantic import RootModel, ValidationError
from pydantic_core import ErrorDetails

from questionpy_sdk.webserver.errors import DetailedServerError, format_error

log = logging.getLogger("questionpy-sdk:web-server")


def dump_detailed_server_error_text(exc: Exception, details: str | list[ErrorDetails] | None = None) -> str:
    detailed_err = DetailedServerError(type(exc).__name__, details)
    return RootModel(detailed_err).model_dump_json()


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
        text = dump_detailed_server_error_text(err, err.errors())
        raise HTTPBadRequest(text=text, content_type="application/json") from err
    except web.HTTPException as exc:
        # Pass through but return JSON
        exc.content_type = "application/json"
        exc.text = dump_detailed_server_error_text(exc, exc.text)
        raise
    except Exception as err:
        log.exception("Server error")
        text = dump_detailed_server_error_text(err, format_error(err))
        raise HTTPInternalServerError(text=text, content_type="application/json") from err


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
