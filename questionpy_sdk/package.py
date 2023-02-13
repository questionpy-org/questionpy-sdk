import logging
from pathlib import Path
from zipfile import ZipFile

from questionpy_common.manifest import Manifest


log = logging.getLogger(__name__)


class PackageBuilder(ZipFile):
    def __init__(self, path: Path, manifest: Manifest):
        super().__init__(path, "w")
        self._manifest = manifest
        self._directory = Path(self._manifest.namespace) / self._manifest.short_name

    def write_manifest(self) -> None:
        log.info("qpy_manifest.json: %s", self._manifest)
        self.writestr("qpy_manifest.json", self._manifest.json())

    def write_glob(self, source_dir: Path, glob: str, prefix: str = "") -> None:
        for source_file in source_dir.glob(glob):
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.info("%s: %s", path_in_pkg, source_file)
            self.write(source_file, self._directory / path_in_pkg)
