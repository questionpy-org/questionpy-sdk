import datetime
import shutil
import tempfile
import zipfile
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from pathlib import Path
from typing import NoReturn, Self

from pathspec import PathSpec

from questionpy_common.constants import DIST_DIR
from questionpy_sdk.package.source import PackageSource


class BuildTarget(AbstractContextManager["BuildTarget"], ABC):
    @property
    @abstractmethod
    def dist(self) -> Path:
        pass

    @abstractmethod
    def maybe_copy_source(self, package_source: PackageSource, ignore_spec: PathSpec) -> None:
        pass


class ZipBuildTarget(BuildTarget):
    _COMPRESS_TYPE = zipfile.ZIP_DEFLATED
    _LOCAL_TIMEZONE = datetime.datetime.now(datetime.UTC).astimezone().tzinfo

    def __init__(self, out_path: Path) -> None:
        self._out_path = out_path

        self._temp_dist: Path | None = None
        self._zipfile: zipfile.ZipFile | None = None

    def __enter__(self) -> Self:
        if not self._temp_dist:
            self._temp_dist = Path(tempfile.mkdtemp(prefix="qpy-build-"))
        if not self._zipfile:
            self._zipfile = zipfile.ZipFile(self._out_path, mode="w")
        return self

    def __exit__(self, *_: object) -> None:
        if not self._zipfile or not self._temp_dist:
            self._raise_not_entered()

        self._mkdir(DIST_DIR)
        for entry in self.dist.glob("**/*"):
            path_in_pkg = DIST_DIR / entry.relative_to(self.dist)

            if entry.is_dir():
                self._mkdir(path_in_pkg.as_posix())
            else:
                self._zipfile.write(entry, path_in_pkg, compress_type=self._COMPRESS_TYPE)

        self._zipfile.close()

        shutil.rmtree(self._temp_dist)

    @property
    def dist(self) -> Path:
        if not self._temp_dist:
            self._raise_not_entered()
        return self._temp_dist

    def maybe_copy_source(self, package_source: PackageSource, ignore_spec: PathSpec) -> None:
        if not self._zipfile:
            self._raise_not_entered()

        for entry in package_source.path.glob("**/*"):
            path_in_pkg = entry.relative_to(package_source.path)

            if path_in_pkg.parts[0] == DIST_DIR or ignore_spec.match_file(path_in_pkg):
                continue

            if entry.is_dir():
                self._mkdir(path_in_pkg.as_posix())
            else:
                self._zipfile.write(entry, path_in_pkg, compress_type=self._COMPRESS_TYPE)

    def _mkdir(self, dest_path: str) -> None:
        if not self._zipfile:
            self._raise_not_entered()

        if not dest_path.endswith("/"):
            dest_path += "/"
        if dest_path in self._zipfile.namelist():
            # Dir already exists, which is fine.
            return

        # use `ZipInfo`, otherwise the directory entry ends up with timestamp 0
        zipinfo = zipfile.ZipInfo(dest_path, date_time=datetime.datetime.now(self._LOCAL_TIMEZONE).timetuple()[:6])
        zipinfo.compress_type = self._COMPRESS_TYPE
        zipinfo.CRC = 0  # TODO: remove once bug is resolved (https://github.com/python/cpython/issues/119052)
        # There is a great summary of the external attributes field here: https://unix.stackexchange.com/a/14727
        zipinfo.external_attr = 0o40755 << 16  # Unix mode drwxr-xr-x
        zipinfo.external_attr |= 0b10000  # DOS directory attribute
        self._zipfile.mkdir(zipinfo)

    def _raise_not_entered(self) -> NoReturn:
        msg = f"ZipBuildTarget '{self._out_path}' was not entered."
        raise RuntimeError(msg)


class DirBuildTarget(BuildTarget):
    def __init__(self, dist_path: Path) -> None:
        self._dist_path = dist_path

    @classmethod
    def in_source(cls, package_source: PackageSource | Path) -> Self:
        if isinstance(package_source, PackageSource):
            package_source = package_source.path
        return cls(package_source / DIST_DIR)

    @property
    def dist(self) -> Path:
        return self._dist_path

    def maybe_copy_source(self, package_source: PackageSource, ignore_spec: PathSpec) -> None:
        # Not supported.
        pass

    def __enter__(self) -> Self:
        if self._dist_path.exists():
            shutil.rmtree(self._dist_path)
        self._dist_path.mkdir(parents=True)
        return self

    def __exit__(self, *_: object) -> None:
        # No cleanup
        pass
