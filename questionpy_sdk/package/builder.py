#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import inspect
import logging
import subprocess
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import questionpy
from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_sdk.models import BuildHookName
from questionpy_sdk.package.errors import PackageBuildError
from questionpy_sdk.package.source import PackageSource

log = logging.getLogger(__name__)


class PackageBuilder(ZipFile):
    """Builds `.qpy` packages.

    This class creates QuestionPy packages from a
    [`PackageSource`][questionpy_sdk.package.source.PackageSource].
    """

    def __init__(self, file: PathLike, source: PackageSource):
        """Opens a package file for writing.

        Args:
            file: Package output path.
            source: Package source.
        """
        super().__init__(file, "w")
        self._source = source

    def write_package(self) -> None:
        """Writes the `.qpy` package to the filesystem.

        Raises:
            PackageBuildError: If the package failed to build.
        """
        self._run_build_hooks("pre")
        self._install_questionpy()
        self._install_requirements()
        self._write_package_files()
        self._write_manifest()
        self._run_build_hooks("post")

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
        # TODO: Exclude __pycache__, pyc files and the like.
        self._write_glob(package_dir, "**/*.py", prefix=f"dependencies/site-packages/{questionpy.__name__}")

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
                self._write_glob(Path(tempdir), "**/*", prefix="dependencies/site-packages")
        except subprocess.CalledProcessError as exc:
            msg = f"Failed to install requirements: {exc.stderr.decode()}"
            raise PackageBuildError(msg) from exc

    def _write_package_files(self) -> None:
        """Writes custom package files."""
        self._write_glob(self._source.path, "python/**/*")
        self._write_glob(self._source.path, "static/**/*")
        self._write_glob(self._source.path, "js/**/*")

    def _write_manifest(self) -> None:
        """Writes package manifest."""
        log.info("%s: %s", MANIFEST_FILENAME, self._source.config)
        self.writestr(MANIFEST_FILENAME, self._source.config.manifest.model_dump_json())

    def _write_glob(self, source_dir: Path, glob: str, prefix: str = "") -> None:
        for source_file in source_dir.glob(glob):
            path_in_pkg = prefix / source_file.relative_to(source_dir)
            log.info("%s: %s", path_in_pkg, source_file)
            self.write(source_file, path_in_pkg)

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
            log.info("%s hook[%d] failed: '%s'", hook_name, num, cmd)
            msg = f"{hook_name} hook[{num}] failed: '{cmd}'"
            raise PackageBuildError(msg)
