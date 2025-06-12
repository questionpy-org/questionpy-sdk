#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING

from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_server.worker import PackageFileData

if TYPE_CHECKING:
    from questionpy_server.worker import Worker


class FilesController(BaseController):
    async def get_static_file(self, path: str) -> PackageFileData:
        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            return await worker.get_static_file(path)

    def get_manifest(self) -> Manifest:
        return self._manifest
