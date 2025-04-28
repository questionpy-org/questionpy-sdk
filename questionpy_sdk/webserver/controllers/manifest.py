#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.controllers.base import BaseController


class ManifestController(BaseController):
    def get_manifest(self) -> Manifest:
        return self._manifest
