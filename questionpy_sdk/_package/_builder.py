import asyncio
import inspect
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Mapping
from mimetypes import guess_type
from pathlib import Path
from typing import ClassVar

import babel
import babel.messages.frontend
from pathspec import GitIgnoreSpec, PathSpec

import questionpy
from questionpy import i18n
from questionpy_common import PackageNamespaceAndShortName
from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_common.dependencies import DependencySolution
from questionpy_common.manifest import (
    DistDynamicQPyDependency,
    DistStaticQPyDependency,
    LockedDependencyInfo,
    Manifest,
    PackageFile,
)
from questionpy_sdk._i18n_utils import bcp47_to_posix
from questionpy_sdk._package._ignores import create_ignore_spec
from questionpy_sdk._package._targets import BuildTarget, DirBuildTarget
from questionpy_sdk._package._validate import (
    validate_dist_structure,
    validate_package_name_and_description,
    validate_requested_lms_attributes,
)
from questionpy_sdk._package.errors import PackageBuildError
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.models import (
    AbstractDynamicQPyDependency,
    BuildHookName,
    PackageConfig,
    SourceDynamicQPyDependency,
    SourceStaticQPyDependency,
)
from questionpy_server.dependencies import (
    DynamicDependencyResolver,
    NoopDependencyResolver,
    resolve_dependency_tree,
)
from questionpy_server.hash import calculate_hash
from questionpy_server.utils.manifest import read_manifest_from_zip

_log = logging.getLogger(__name__)

_PYTHON_TEMP_PATHS = GitIgnoreSpec.from_lines(("*.pyc", "__pycache__"))


class PackageBuilder:
    STATIC_FILE_GLOBS: ClassVar[set[str]] = {"css/**/*", "js/**/*", "assets/**/*"}

    def __init__(
        self,
        source: PackageSource,
        target: BuildTarget,
        *,
        copy_sources: bool,
        dependency_resolver: DynamicDependencyResolver,
    ) -> None:
        self._source = source
        self._target = target

        self._static_path = self._target.dist / "static"

        self._copy_sources = copy_sources

        source_manifest = self._source.config.to_manifest()
        self._manifest = Manifest(**source_manifest.model_dump())

        self._ignore_spec = create_ignore_spec(self._source.path, self._source.config.ignore)

        self._dynamic_dep_resolver = dependency_resolver

    def write_package(self) -> None:
        """Writes the package to the filesystem.

        Raises:
            PackageBuildError: If the package failed to build.
        """
        self._run_build_hooks("pre")
        self._install_questionpy()
        self._install_requirements()
        static_deps = self._install_static_qpy_dependencies()
        self._lock_dynamic_dependencies(static_deps)
        self._write_package_files()
        self._compile_pos()
        if self._copy_sources:
            self._copy_source_files()
        self._run_build_hooks("post")
        self._handle_generated_static_files()
        self._write_manifest()

        validate_dist_structure(self._manifest, self._target.dist)
        validate_requested_lms_attributes(self._manifest)
        validate_package_name_and_description(self._manifest)

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

    def _install_static_qpy_dependencies(self) -> dict[Path, DistStaticQPyDependency]:
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

        installed_deps: dict[Path, DistStaticQPyDependency] = {}

        # Then, we copy all of their contents into a directory in dist/dependencies/qpy.
        for dep_path in dependency_paths:
            _log.info("Copying static QPy dependency '%s'", dep_path)

            with dep_path.open("rb+") as dep_package_file, zipfile.ZipFile(dep_package_file) as dep_package_zf:
                dep_hash = calculate_hash(dep_package_file)
                dep_manifest = asyncio.run(read_manifest_from_zip(dep_path))

                dep_dir_name = f"{dep_manifest.namespace}-{dep_manifest.short_name}-{dep_manifest.version}"
                dest_path = self._target.dist / "dependencies" / "qpy" / dep_dir_name
                dep_package_zf.extractall(dest_path)

            dist_dep = DistStaticQPyDependency(
                namespace=dep_manifest.namespace,
                short_name=dep_manifest.short_name,
                version=str(dep_manifest.version),
                dependencies=dep_manifest.dependencies,
                hash=dep_hash,
            )

            installed_deps[dep_path] = dist_dep
            self._manifest.dependencies.qpy.append(dist_dep)

        return installed_deps

    def _lock_dynamic_dependencies(self, static_dependencies: dict[Path, DistStaticQPyDependency]) -> None:
        # Even when no dynamic dependencies use locking, resolve_dependency_tree checks the tree for consistency.
        resolution = _resolve_dependencies_for_packaging(
            self._source.config, self._dynamic_dep_resolver, static_dependencies
        )

        for source_dep in self._source.config.dependencies.qpy:
            if not isinstance(source_dep, SourceDynamicQPyDependency):
                continue

            lock_strategy = source_dep.lock
            if lock_strategy is None:
                lock_strategy = self._source.config.lock_dependencies

            if not lock_strategy:
                lock_info = None
            else:
                chosen_version = resolution[PackageNamespaceAndShortName(source_dep.namespace, source_dep.short_name)]
                lock_info = LockedDependencyInfo(
                    strategy=lock_strategy,
                    locked_version=str(chosen_version.version),
                    locked_hash=chosen_version.hash,
                )

            self._manifest.dependencies.qpy.append(
                DistDynamicQPyDependency(
                    **AbstractDynamicQPyDependency.model_dump(source_dep),
                    locked=lock_info,
                )
            )

    def _write_package_files(self) -> None:
        """Writes custom package files."""
        self._copy_glob(self._source.path, "python/**/*", self._target.dist)
        self._copy_glob(self._source.path, "templates/**/*", self._target.dist)

        for glob in self.STATIC_FILE_GLOBS:
            self._copy_glob(self._source.path, glob, self._static_path, add_to_static_files=True)

    def _add_to_static_files(self, path: Path) -> bool:
        """Adds a file to the static files list in the manifest."""
        if not path.is_file():
            return False

        path_in_dist = str(path.relative_to(self._target.dist))
        if path_in_dist in self._manifest.static_files:
            return False

        mime_type = guess_type(path)[0]
        file_size = path.stat().st_size
        self._manifest.static_files[path_in_dist] = PackageFile(mime_type=mime_type, size=file_size)
        return True

    def _handle_generated_static_files(self) -> None:
        """Handles generated package files."""
        for glob in self.STATIC_FILE_GLOBS:
            for path in self._static_path.glob(glob):
                if self._add_to_static_files(path) and _log.isEnabledFor(logging.DEBUG):
                    relative_path = path.relative_to(self._target.dist)
                    _log.debug("Added generated static file to manifest: %s", relative_path)

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
            if add_to_static_files:
                self._add_to_static_files(dest_path)


def build_qpy_package(
    source: PackageSource,
    target: BuildTarget | None = None,
    *,
    copy_sources: bool = True,
    dependency_resolver: DynamicDependencyResolver | None = None,
) -> None:
    if not dependency_resolver:
        dependency_resolver = NoopDependencyResolver()

    if not target:
        target = DirBuildTarget.in_source(source)

    with target:
        builder = PackageBuilder(source, target, copy_sources=copy_sources, dependency_resolver=dependency_resolver)
        builder.write_package()


def _resolve_dependencies_for_packaging(
    config: PackageConfig,
    dynamic_resolver: DynamicDependencyResolver,
    source_static_deps: Mapping[Path, DistStaticQPyDependency],
) -> dict[PackageNamespaceAndShortName, DependencySolution]:
    """Converts `SourceQPyDependency` models from the `PackageConfig` into `DistQPyDependency` models.

    `DistStaticQPyDependency` models were already built when the static dependencies were installed, and we can build
    `DistDynamicQPyDependency` by just copying the `SourceDynamicQPyDependency`.
    """
    root_deps = [
        dep
        if isinstance(dep, (DistStaticQPyDependency, DistDynamicQPyDependency))
        else source_static_deps[dep.path]
        if isinstance(dep, SourceStaticQPyDependency)
        else DistDynamicQPyDependency(**dep.model_dump())
        for dep in config.dependencies.qpy
    ]

    return resolve_dependency_tree(config, root_deps, dynamic_resolver)
