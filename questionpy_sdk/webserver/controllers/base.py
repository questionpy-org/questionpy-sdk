#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Literal, overload

from yarl import URL

from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.controllers.errors import MissingQuestionStateError
from questionpy_sdk.webserver.state import StateManager
from questionpy_server.worker import Worker

if TYPE_CHECKING:
    from questionpy_sdk.webserver import WebServer


class BaseController:
    def __init__(self, webserver: "WebServer") -> None:
        self._webserver = webserver

    def generate_api_url(self, name: str, **kwargs: str) -> URL:
        return self._webserver.api_app.router[name].url_for(**kwargs)

    @asynccontextmanager
    async def get_worker(self) -> AsyncIterator[Worker]:
        async with self._webserver.worker_pool.get_worker(
            self._webserver.package_location, 0, None, self._webserver.worker_permissions
        ) as worker:
            yield worker

    @property
    def _manifest(self) -> Manifest:
        return self._webserver.manifest

    @property
    def _state_manager(self) -> StateManager:
        return self._webserver.state_manager

    @overload
    async def _get_question_state(self, *, allow_missing: Literal[False] = ...) -> str: ...

    @overload
    async def _get_question_state(self, *, allow_missing: Literal[True]) -> str | None: ...

    async def _get_question_state(self, *, allow_missing: bool = False) -> str | None:
        try:
            return await self._state_manager.read_question_state()
        except FileNotFoundError as err:
            if allow_missing:
                return None
            raise MissingQuestionStateError from err
