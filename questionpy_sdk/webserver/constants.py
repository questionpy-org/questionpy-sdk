#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import os
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

from questionpy_common.environment import RequestUser
from questionpy_common.manifest import Bcp47LanguageTag

if TYPE_CHECKING:
    from questionpy_sdk.webserver import WebServer

API_PATH_PREFIX = "/api"
ID_RE = r"[A-Za-z0-9_-]{8}"

WEBSERVER_KEY: web.AppKey["WebServer"] = web.AppKey("qpy_webserver")
REQUEST_CONTROLLER_KEY = "qpy_controller"

DEFAULT_REQUEST_USER = RequestUser([Bcp47LanguageTag("de"), Bcp47LanguageTag("en")])
USE_VITE_DEV_SERVER = os.getenv("USE_VITE_DEV_SERVER") in {"true", "TRUE", "1"}
STATIC_DIR = Path(__file__).parent / "static"
