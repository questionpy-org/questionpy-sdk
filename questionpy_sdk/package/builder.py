#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import datetime
import inspect
import logging
import shutil
import subprocess
import zipfile
from abc import abstractmethod
from contextlib import AbstractContextManager
from mimetypes import guess_type
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType

import questionpy
from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_common.manifest import Manifest, PackageFile
from questionpy_sdk.models import BuildHookName
from questionpy_sdk.package.errors import PackageBuildError
from questionpy_sdk.package.source import PackageSource

log = logging.getLogger(__name__)


class PackageBuilderBase(AbstractContextManager):
    """Builds a QuestionPy package.

    This class creates QuestionPy packages from a
    [`PackageSource`][questionpy_sdk.package.source.PackageSource].
    """

    def __init__(self, source: PackageSource, *, copy_sources: bool):
        self._source = source
        self._copy_sources = copy_sources
        self._static_files: dict[str, PackageFile] = {}

    def write_package(self) -> None:
        """Writes the package to the filesystem.

        Raises:
            PackageBuildError: If the package failed to build.
        """
        self._prepare()
        self._run_build_hooks("pre")
        self._install_questionpy()
        self._install_requirements()
        self._write_package_files()
        self._write_manifest()
        if self._copy_sources:
            self._copy_source_files()
        self._run_build_hooks("post")

    def _prepare(self) -> None:
        pass

    def _run_build_hooks(self, hook_name: BuildHookName) -> None:
        commands = self._source.config.build_hooks.get(hook_name, [])

        if isinstance(commands, str):
            commands = [commands]

        for idx, cmd in enumerate(commands):
            self._run_hook(cmd, hook_name, idx)

    def _install_questionpy(self) -> None:
        """Adds the `questionpy` module to the package."""
        # getfile returns the path to the package's __init__.py
        package_dir = Path(inspect.getfile(questionpy)).parent
        prefix = Path(DIST_DIR) / "dependencies" / "site-packages" / questionpy.__name__
        self._write_glob(package_dir, "**/*", prefix)

    def _install_requirements(self) -> None:
        """Adds package requirements."""
        config = self._source.config

        # treat as relative reference to a requirements.txt and read those
        if isinstance(config.requirements, str):
            pip_args = ["-r", str(self._source.path / config.requirements)]

        # treat as individual dependency specifiers
        elif isinstance(config.requirements, list):
            pip_args = config.requirements

        # no dependencies specified
        else:
            return

        # pip doesn't offer a public API, so we have to resort to subprocess (pypa/pip#3121)
        try:
            with TemporaryDirectory(prefix=f"qpy_{config.short_name}") as tempdir:
                subprocess.run(["pip", "install", "--target", tempdir, *pip_args], check=True, capture_output=True)  # noqa: S603, S607
                self._write_glob(Path(tempdir), "**/*", Path(DIST_DIR) / "dependencies" / "site-packages")
        except subprocess.CalledProcessError as exc:
            msg = f"Failed to install requirements: {exc.stderr.decode()}"
            raise PackageBuildError(msg) from exc

    def _write_package_files(self) -> None:
        """Writes custom package files."""
        static_path = Path(DIST_DIR) / "static"
        self._write_glob(self._source.path, "python/**/*", DIST_DIR)
        self._write_glob(self._source.path, "css/**/*", static_path, add_to_static_files=True)
        self._write_glob(self._source.path, "js/**/*", static_path, add_to_static_files=True)
        self._write_glob(self._source.path, "static/**/*", DIST_DIR, add_to_static_files=True)

    def _write_manifest(self) -> None:
        """Writes package manifest."""
        build_manifest_path = Path(DIST_DIR) / MANIFEST_FILENAME
        source_manifest = self._source.config.manifest
        manifest = Manifest(**source_manifest.model_dump(), static_files=self._static_files)
        log.debug("%s: %s", MANIFEST_FILENAME, manifest)
        self._write_string(build_manifest_path, manifest.model_dump_json())

    def _run_hook(self, cmd: str, hook_name: BuildHookName, num: int) -> None:
        log.info("Running %s hook[%d]: '%s'", hook_name, num, cmd)
        proc = subprocess.Popen(
            cmd,
            cwd=self._source.path,
            shell=True,  # noqa: S602
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.stdout:
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                log.info("%s hook[%d]: %s", hook_name, num, line.rstrip())
        return_code = proc.wait()
        if return_code != 0:
            log.error("%s hook[%d] failed: '%s'", hook_name, num, cmd)
            msg = f"{hook_name} hook[{num}] failed: '{cmd}'"
            raise PackageBuildError(msg)

    def _copy_source_files(self) -> None:
        for source_file in self._source.path.glob("**/*"):
            path_in_pkg = source_file.relative_to(self._source.path)
            if self._skip_file(source_file) or path_in_pkg.parts[0] == DIST_DIR:
                continue
            log.debug("%s: %s", source_file, path_in_pkg)
            self._write_file(source_file, path_in_pkg)

    def _write_glob(
        self, source_dir: Path, glob: str, prefix: str | Path = "", *, add_to_static_files: bool = False
    ) -> None:
        for source_file in source_dir.glob(glob):
            if self._skip_file(source_file):
                continue
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.debug("%s: %s", path_in_pkg, source_file)
            self._write_file(source_file, path_in_pkg)

            # register as static file in build manifest
            if add_to_static_files:
                mime_type = guess_type(source_file)[0]
                file_size = source_file.stat().st_size
                path_in_dist = str(path_in_pkg.relative_to(DIST_DIR))
                self._static_files[path_in_dist] = PackageFile(mime_type=mime_type, size=file_size)

    @staticmethod
    def _skip_file(path: Path) -> bool:
        return "__pycache__" in path.parts

    @abstractmethod
    def _write_file(self, source_path: Path, dest_path: Path) -> None:
        pass

    @abstractmethod
    def _write_string(self, dest_path: Path, content: str) -> None:
        pass

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        return None


class DirPackageBuilder(PackageBuilderBase):
    """Builds a package to a `dist` directory."""

    def __init__(self, source: PackageSource):
        """Opens a source directory for writing.

        Args:
            source: Package source.
        """
        super().__init__(source, copy_sources=False)

    def _prepare(self) -> None:
        super()._prepare()

        # clear dist dir before building
        dist_path = self._source.path / DIST_DIR
        if dist_path.is_dir():
            shutil.rmtree(dist_path)

    def _write_file(self, source_path: Path, dest_path: Path) -> None:
        if not source_path.is_dir():
            abs_dest_path = self._source.path / dest_path
            self._ensure_target_dir(abs_dest_path)
            shutil.copy(source_path, abs_dest_path)

    def _write_string(self, dest_path: Path, content: str) -> None:
        abs_dest_path = self._source.path / dest_path
        self._ensure_target_dir(abs_dest_path)
        abs_dest_path.write_text(content)

    def _ensure_target_dir(self, path: Path) -> None:
        path.parent.mkdir(exist_ok=True, parents=True)


class ZipPackageBuilder(PackageBuilderBase):
    """Builds `.qpy` package file."""

    COMPRESS_TYPE = zipfile.ZIP_DEFLATED

    def __init__(self, output_path: PathLike, source: PackageSource, *, copy_sources: bool = True):
        """Opens a package file for writing.

        Args:
            output_path: Package output path.
            source: Package source.
            copy_sources: Copy sources into archive.
        """
        super().__init__(source, copy_sources=copy_sources)
        self._zipfile = zipfile.ZipFile(output_path, mode="w", compression=self.COMPRESS_TYPE)

    def _write_file(self, source_path: Path, dest_path: Path) -> None:
        self._ensure_directory_entries(dest_path)
        self._zipfile.write(source_path, dest_path, compress_type=self.COMPRESS_TYPE)

    def _write_string(self, dest_path: Path, content: str) -> None:
        self._ensure_directory_entries(dest_path)
        self._zipfile.writestr(str(dest_path), content, compress_type=self.COMPRESS_TYPE)

    def _ensure_directory_entries(self, path: Path) -> None:
        """Ensure directory entries up to `path` are created."""
        tz = datetime.datetime.now().astimezone().tzinfo
        for parent in reversed(path.parents):
            strpath = str(parent)
            if not strpath.endswith("/"):
                strpath += "/"
            if len(parent.parts) > 0 and all(strpath != fn.filename for fn in self._zipfile.infolist()):
                # use `ZipInfo`, otherwise the directory entry ends up with timestamp 0
                zipinfo = zipfile.ZipInfo(strpath, date_time=datetime.datetime.now(tz).timetuple()[:6])
                zipinfo.compress_type = self.COMPRESS_TYPE
                zipinfo.CRC = 0  # TODO: remove once bug is resolved (https://github.com/python/cpython/issues/119052)
                self._zipfile.mkdir(zipinfo)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self._zipfile.__exit__(exc_type, exc_value, traceback)
