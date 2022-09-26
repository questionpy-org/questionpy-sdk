import logging
from pathlib import Path
from zipfile import ZipFile

from questionpy_common.manifest import Manifest


log = logging.getLogger(__name__)


class PackageBuilder(ZipFile):
    def __init__(self, path: Path):
        super().__init__(path, "w")

    def write_manifest(self, manifest: Manifest) -> None:
        log.info("qpy_manifest.json: %s", manifest)
        self.writestr("qpy_manifest.json", manifest.json())

    def write_glob(self, prefix: str, source_dir: Path, glob: str) -> None:
        for source_file in source_dir.glob(glob):
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.info("%s: %s", path_in_pkg, source_file)
            self.write(source_file, path_in_pkg)
