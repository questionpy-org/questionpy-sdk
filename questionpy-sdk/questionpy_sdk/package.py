import logging
from functools import cached_property
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from questionpy import Manifest

log = logging.getLogger(__name__)


class QPyPackage(ZipFile):
    def __init__(self, path: Path, mode: Literal["r", "w"]):
        super().__init__(path, mode)

    def write_manifest(self, manifest: Manifest) -> None:
        log.info("qpy_manifest.yml: %s", manifest)
        self.writestr("qpy_manifest.yml", manifest.yaml())

    def write_glob(self, prefix: str, source_dir: Path, glob: str) -> None:
        for source_file in source_dir.glob(glob):
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.info("%s: %s", path_in_pkg, source_file)
            self.write(source_file, path_in_pkg)

    @cached_property
    def manifest(self) -> Manifest:
        return Manifest.parse_raw(self.read("qpy_manifest.yml"))
