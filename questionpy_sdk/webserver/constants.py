#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from enum import StrEnum
from typing import TYPE_CHECKING

from aiohttp import web

from questionpy_common.environment import RequestUser
from questionpy_common.manifest import Bcp47LanguageTag

if TYPE_CHECKING:
    from .app import WebServer

API_PATH_PREFIX = "/api"

WEBSERVER_KEY: web.AppKey["WebServer"] = web.AppKey("webserver")

DEFAULT_REQUEST_USER = RequestUser([Bcp47LanguageTag("de"), Bcp47LanguageTag("en")])


class StateFilename(StrEnum):
    QUESTION_STATE = "question_state.txt"
    ATTEMPT_STATE = "attempt_state.txt"
    ATTEMPT_SEED = "attempt_seed.txt"
    SCORE = "score.json"
    LAST_ATTEMPT_DATA = "last_attempt_data.json"
