#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from typing import TYPE_CHECKING

from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_server.worker import PackageFileData

if TYPE_CHECKING:
    from questionpy_server.worker import Worker


class FileController(BaseController):
    async def get_static_file(self, namespace: str, short_name: str, path: str) -> PackageFileData:
        if self._manifest.namespace != namespace or self._manifest.short_name != short_name:
            # TODO: Support static files in non-main packages by using namespace and short_name.
            msg = "Static file retrieval from non-main packages is not supported yet."
            raise ValueError(msg)

        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            return await worker.get_static_file(path)
