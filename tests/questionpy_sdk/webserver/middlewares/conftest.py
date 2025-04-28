#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest
from aiohttp import web

from questionpy_sdk.webserver.constants import WEBSERVER_KEY

if TYPE_CHECKING:
    from questionpy_sdk.webserver.server import WebServer


@pytest.fixture
def app() -> web.Application:
    app = web.Application()
    app[WEBSERVER_KEY] = cast("WebServer", Mock())
    return app
