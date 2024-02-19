#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from pathlib import Path
from zipfile import ZipFile

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_sdk.models import PackageConfig


log = logging.getLogger(__name__)


class PackageBuilder(ZipFile):
    def __init__(self, path: Path):
        super().__init__(path, "w")

    def write_manifest(self, config: PackageConfig) -> None:
        log.info("%s: %s", MANIFEST_FILENAME, config)
        self.writestr(MANIFEST_FILENAME, config.manifest.model_dump_json())

    def write_glob(self, source_dir: Path, glob: str, prefix: str = "") -> None:
        for source_file in source_dir.glob(glob):
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.info("%s: %s", path_in_pkg, source_file)
            self.write(source_file, path_in_pkg)
