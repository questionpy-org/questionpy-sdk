import inspect
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from hashlib import file_digest
from mimetypes import guess_type
from pathlib import Path

import babel
import babel.messages.frontend
from pathspec import GitIgnoreSpec, PathSpec

import questionpy
from questionpy import i18n
from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_common.manifest import DistStaticQPyDependency, Manifest, PackageFile
from questionpy_sdk._i18n_utils import bcp47_to_posix
from questionpy_sdk._package._ignores import create_ignore_spec
from questionpy_sdk._package._targets import BuildTarget, DirBuildTarget
from questionpy_sdk._package._validate import validate_dist_structure
from questionpy_sdk._package.errors import PackageBuildError
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.models import BuildHookName, SourceStaticQPyDependency

_log = logging.getLogger(__name__)

_PYTHON_TEMP_PATHS = GitIgnoreSpec.from_lines(("*.pyc", "__pycache__"))


class PackageBuilder:
    def __init__(self, source: PackageSource, target: BuildTarget, *, copy_sources: bool) -> None:
        self._source = source
        self._target = target

        self._copy_sources = copy_sources

        source_manifest = self._source.config.to_manifest()
        self._manifest = Manifest(**source_manifest.model_dump())

        self._ignore_spec = create_ignore_spec(self._source.path, self._source.config.ignore)

    def write_package(self) -> None:
        """Writes the package to the filesystem.

        Raises:
            PackageBuildError: If the package failed to build.
        """
        self._run_build_hooks("pre")
        self._install_questionpy()
        self._install_requirements()
        self._install_static_qpy_dependencies()
        self._write_package_files()
        self._compile_pos()
        self._write_manifest()
        if self._copy_sources:
            self._copy_source_files()
        self._run_build_hooks("post")

        validate_dist_structure(self._manifest, self._target.dist)

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
        prefix = self._target.dist / "dependencies" / "site-packages" / questionpy.__name__
        self._copy_glob(package_dir, "**/*", prefix, ignore_paths=_PYTHON_TEMP_PATHS)

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
            with tempfile.TemporaryDirectory(prefix=f"qpy_{config.short_name}") as tempdir:
                subprocess.run(  # noqa: S603 # Not really applicable here.
                    ["pip", "install", "--target", tempdir, *pip_args],  # noqa: S607
                    check=True,
                    capture_output=True,
                )
                self._copy_glob(
                    Path(tempdir),
                    "**/*",
                    self._target.dist / "dependencies" / "site-packages",
                    ignore_paths=_PYTHON_TEMP_PATHS,
                )
        except subprocess.CalledProcessError as exc:
            msg = f"Failed to install requirements: {exc.stderr.decode()}"
            raise PackageBuildError(msg) from exc

    def _install_static_qpy_dependencies(self) -> None:
        # Ignoring duplicates, we collect all the dependencies in the dependencies directory and those explicitly
        # listed.
        dependency_paths = set((self._source.path / "dependencies").glob("*.qpy"))
        for dep in self._source.config.dependencies.qpy:
            if not isinstance(dep, SourceStaticQPyDependency):
                continue

            dep_path = dep.path if dep.path.is_absolute() else (self._source.path / dep.path)
            if not dep_path.exists():
                msg = f"The specified dependency '{dep.path}' does not exist."
                raise PackageBuildError(msg)

            dependency_paths.add(dep_path)

        # Then, we copy all of their contents into a directory in dist/dependencies/qpy.
        for dep_path in dependency_paths:
            _log.info("Copying static QPy dependency '%s'", dep_path)

            with dep_path.open("rb+") as dep_package_file, zipfile.ZipFile(dep_package_file) as dep_package_zf:
                dep_hash = file_digest(dep_package_file, "sha256").hexdigest()
                dep_manifest = Manifest.model_validate_json(dep_package_zf.read(f"{DIST_DIR}/{MANIFEST_FILENAME}"))
                dep_dir_name = f"{dep_manifest.namespace}-{dep_manifest.short_name}-{dep_manifest.version}"

                dest_path = self._target.dist / "dependencies" / "qpy" / dep_dir_name
                dep_package_zf.extractall(dest_path)

            self._manifest.dependencies.qpy.append(DistStaticQPyDependency(dir_name=dep_dir_name, hash=dep_hash))

    def _write_package_files(self) -> None:
        """Writes custom package files."""
        self._copy_glob(self._source.path, "python/**/*", self._target.dist)
        self._copy_glob(self._source.path, "templates/**/*", self._target.dist)

        static_path = self._target.dist / "static"
        self._copy_glob(self._source.path, "css/**/*", static_path, add_to_static_files=True)
        self._copy_glob(self._source.path, "js/**/*", static_path, add_to_static_files=True)
        self._copy_glob(self._source.path, "assets/**/*", static_path, add_to_static_files=True)
        self._copy_glob(self._source.path, "logo.svg", static_path / "assets", add_to_static_files=True)
        self._copy_glob(self._source.path, "logo.png", static_path / "assets", add_to_static_files=True)
        self._copy_glob(self._source.path, "logo.jpg", static_path / "assets", add_to_static_files=True)

    def _write_manifest(self) -> None:
        """Writes package manifest."""
        _log.debug("%s: %s", MANIFEST_FILENAME, self._manifest)
        (self._target.dist / MANIFEST_FILENAME).write_text(self._manifest.model_dump_json())

    def _run_hook(self, cmd: str, hook_name: BuildHookName, num: int) -> None:
        _log.info("Running %s hook[%d]: '%s'", hook_name, num, cmd)

        env = {
            **os.environ,
            "QPY_DIST": str(self._target.dist.absolute()),
            "QPY_DIST_JS": str(self._target.dist.absolute() / "static" / "js"),
            "QPY_DIST_CSS": str(self._target.dist.absolute() / "static" / "css"),
            "QPY_SOURCE": str(self._source.path.absolute()),
        }

        with subprocess.Popen(  # noqa: S602
            cmd, cwd=self._source.path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
        ) as proc:
            if proc.stdout:
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    _log.info("%s hook[%d]: %s", hook_name, num, line.rstrip())

        if proc.returncode != 0:
            _log.error("%s hook[%d] failed: '%s'", hook_name, num, cmd)
            msg = f"{hook_name} hook[{num}] failed: '{cmd}'"
            raise PackageBuildError(msg)

    def _copy_source_files(self) -> None:
        if self._copy_sources:
            self._target.maybe_copy_source(self._source, self._ignore_spec)

    def _compile_pos(self) -> None:
        with tempfile.TemporaryDirectory(prefix="qpy_build_locales_") as tempdir_str:
            tempdir = Path(tempdir_str)
            for domain, locale, po_file in self._source.discover_po_files():
                if self._ignore_spec.match_file(po_file.relative_to(self._source.path)):
                    # Apply ignore patterns to .po files.
                    continue

                if po_file.with_suffix(".mo").exists():
                    # By default, Poedit also saves a compiled .mo file, so we warn the user if one exists.
                    _log.warning(
                        "The existing .mo file at '%s' will not be used, '%s' will be compiled instead.",
                        po_file.with_suffix(".mo"),
                        po_file.name,
                    )

                outfile = tempdir / locale / i18n.DEFAULT_CATEGORY / f"{domain}.mo"
                outfile.parent.mkdir(parents=True, exist_ok=True)

                cmd = babel.messages.frontend.CompileCatalog()
                cmd.locale = bcp47_to_posix(locale)
                cmd.input_file = po_file
                cmd.output_file = outfile
                cmd.ensure_finalized()
                cmd.run()

            self._copy_glob(tempdir, "**/*.mo", self._target.dist / "locale", ignore_paths=False)

    def _copy_glob(
        self,
        source_dir: Path,
        glob: str,
        dest_dir: Path,
        *,
        add_to_static_files: bool = False,
        ignore_paths: PathSpec | bool = True,
    ) -> None:
        """Copy everything in `source_dir` matching `glob` to the same relative path under `dest_dir`.

        If `add_to_static_files` is `True`, all copied files will be added to the static files list in the manifest.
        `dest_dir` must be inside the dist dir in that case, or an error will be raised.

        Will respect `self._ignore_spec` unless another PathSpec or `False` is passed in `ignore_path_spec`. `False`
        will cause no files to be ignored.
        """
        if ignore_paths is True:
            ignore_paths = self._ignore_spec

        for source_file in source_dir.glob(glob):
            dest_path = dest_dir / source_file.relative_to(source_dir)

            if ignore_paths and ignore_paths.match_file(source_file.relative_to(source_dir)):
                continue

            _log.debug("%s: %s", dest_path, source_file)

            if source_file.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_path)

            # register as static file in build manifest
            if source_file.is_file() and add_to_static_files:
                mime_type = guess_type(source_file)[0]
                file_size = source_file.stat().st_size
                path_in_dist = str(dest_path.relative_to(self._target.dist))
                self._manifest.static_files[path_in_dist] = PackageFile(mime_type=mime_type, size=file_size)


def build_qpy_package(source: PackageSource, target: BuildTarget | None = None, *, copy_sources: bool = True) -> None:
    if not target:
        target = DirBuildTarget.in_source(source)

    with target:
        builder = PackageBuilder(source, target, copy_sources=copy_sources)
        builder.write_package()
