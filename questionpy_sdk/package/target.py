import datetime
import logging
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath

from pathspec import PathSpec
from questionpy_common.constants import DIST_DIR


class BuildTarget(ABC):
    @abstractmethod
    def package_dist_and_source(self, dist: Path, source: Path) -> Path:
        pass


_log = logging.getLogger(__name__)


class ZipBuildTarget(BuildTarget):
    COMPRESS_TYPE = zipfile.ZIP_DEFLATED

    def __init__(self, path: Path, ignore_spec: PathSpec) -> None:
        self.path = path
        self._ignore_spec = ignore_spec

    def package_dist_and_source(self, dist: Path, source: Path) -> Path:
        with zipfile.ZipFile(self.path, "w") as dest_zipfile:
            self._write_tree(dest_zipfile, dist, PurePosixPath(DIST_DIR))
            self._write_tree(dest_zipfile, source, PurePosixPath("."), self._ignore_spec)

        _log.debug("Wrote ZIP-based package '%s'", self.path)
        return self.path

    def _write_tree(self, dest_zipfile: zipfile.ZipFile, tree_root: Path, dest_root: PurePosixPath,
                    ignore_spec: PathSpec | None = None) -> None:
        for entry in tree_root.glob("**/*"):
            if ignore_spec and ignore_spec.match_file(entry.relative_to(tree_root)):
                continue

            path_in_zip = dest_root / entry.relative_to(tree_root)
            if entry.is_dir():
                self._mkdir(dest_zipfile, path_in_zip)
            else:
                self._ensure_directory_entries(dest_zipfile, path_in_zip)
                dest_zipfile.write(entry, path_in_zip, self.COMPRESS_TYPE)

    def _ensure_directory_entries(self, dest_zipfile: zipfile.ZipFile, path: PurePosixPath) -> None:
        """Ensure directory entries up to `path` are created."""
        for parent in reversed(path.parents):
            if len(parent.parts) > 0:
                self._mkdir(dest_zipfile, parent)

    def _mkdir(self, dest_zipfile: zipfile.ZipFile, dest: PurePosixPath) -> None:
        strpath = str(dest)
        if not strpath.endswith("/"):
            strpath += "/"
        if strpath in dest_zipfile.namelist():
            # Dir already exists, which is fine.
            return

        local_tz = datetime.datetime.now(datetime.UTC).astimezone().tzinfo

        # use `ZipInfo`, otherwise the directory entry ends up with timestamp 0
        zipinfo = zipfile.ZipInfo(strpath, date_time=datetime.datetime.now(local_tz).timetuple()[:6])
        zipinfo.compress_type = self.COMPRESS_TYPE
        zipinfo.CRC = 0  # TODO: remove once bug is resolved (https://github.com/python/cpython/issues/119052)
        # There is a great summary of the external attributes field here: https://unix.stackexchange.com/a/14727
        zipinfo.external_attr = 0o40755 << 16  # Unix mode drwxr-xr-x
        zipinfo.external_attr |= 0b10000  # DOS directory attribute
        dest_zipfile.mkdir(zipinfo)


class DirBuildTarget(BuildTarget):
    pass
