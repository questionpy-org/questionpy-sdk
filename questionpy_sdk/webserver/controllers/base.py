#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING, Literal, overload

from aiohttp import web

from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.state import StateManager
from questionpy_server import WorkerPool

if TYPE_CHECKING:
    from questionpy_sdk.webserver import WebServer
    from questionpy_server.worker.runtime.package_location import PackageLocation


class BaseController:
    def __init__(self, webserver: "WebServer") -> None:
        self._webserver = webserver

    @property
    def _package_location(self) -> "PackageLocation":
        return self._webserver.package_location

    @property
    def _manifest(self) -> Manifest:
        return self._webserver.manifest

    @property
    def _worker_pool(self) -> WorkerPool:
        return self._webserver.worker_pool

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
            raise web.HTTPConflict(text="No question state found") from err
