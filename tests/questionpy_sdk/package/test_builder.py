#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import compileall
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pytest
import yaml

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_common.manifest import Manifest
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.package.builder import DirPackageBuilder, ZipPackageBuilder
from questionpy_sdk.package.errors import PackageBuildError
from questionpy_sdk.package.source import PackageSource


@pytest.fixture
def qpy_pkg_path(tmp_path: Path, source_path: Path) -> Path:
    qpy_path = tmp_path / "package.qpy"
    with ZipPackageBuilder(qpy_path, PackageSource(source_path)) as builder:
        builder.write_package()
    return qpy_path


def test_installs_questionpy(qpy_pkg_path: Path) -> None:
    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/questionpy/__init__.py")


# test a somewhat elusive bug that surfaces when trying to import a module from a zipfile. zipimport appears to
# depend on the existence of explicit directory entries inside the zip file.
def test_creates_proper_directory_entries(qpy_pkg_path: Path) -> None:
    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/python/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/python/local/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/python/local/minimal_example/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/python/local/minimal_example/templates/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/").is_dir()
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/questionpy/").is_dir()

    # actually import from the zip file to make sure things work
    try:
        sys.path.insert(0, str(qpy_pkg_path / f"{DIST_DIR}/python"))
        pkg_module = import_module("local.minimal_example")
        assert callable(pkg_module.init)
    finally:
        sys.path.pop(0)


def test_installs_requirements_list(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["requirements"] = ["attrs==23.2.0", "pytz==2024.1"]
    with config_path.open("w") as f:
        yaml.dump(config, f)

    qpy_pkg_path = tmp_path / "package.qpy"
    with ZipPackageBuilder(qpy_pkg_path, PackageSource(source_path)) as builder:
        builder.write_package()

    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/attrs/__init__.py")
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/pytz/__init__.py")


def test_installs_requirements_txt(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["requirements"] = "requirements.txt"
    with config_path.open("w") as f:
        yaml.dump(config, f)
    with (source_path / "requirements.txt").open("w") as f:
        f.write("attrs==23.2.0\n")
        f.write("pytz==2024.1\n")

    qpy_pkg_path = tmp_path / "package.qpy"
    with ZipPackageBuilder(qpy_pkg_path, PackageSource(source_path)) as builder:
        builder.write_package()

    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/attrs/__init__.py")
        assert zipfile.getinfo(f"{DIST_DIR}/dependencies/site-packages/pytz/__init__.py")


def test_invalid_requirement_raises_error(source_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package_source = PackageSource(source_path)
    package_source.config.requirements = ["this_package_does_not_exist"]

    def mock_run(*_: Any, **__: Any) -> None:
        raise subprocess.CalledProcessError(1, "", stderr=b"some pip error")

    with monkeypatch.context() as mp:
        mp.setattr(subprocess, "run", mock_run)
        with (
            pytest.raises(PackageBuildError) as exc,
            ZipPackageBuilder(tmp_path / "package.qpy", package_source) as builder,
        ):
            builder.write_package()

    assert exc.match("Failed to install requirements")


@pytest.mark.source_pkg("static-files")
def test_writes_package_files(qpy_pkg_path: Path) -> None:
    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/python/local/static_files_example/__init__.py")
        assert zipfile.getinfo(f"{DIST_DIR}/static/css/styles.css")
        assert zipfile.getinfo(f"{DIST_DIR}/static/js/test.js")


@pytest.mark.source_pkg("static-files")
def test_writes_manifest(qpy_pkg_path: Path) -> None:
    with ZipFile(qpy_pkg_path) as zipfile, zipfile.open(f"{DIST_DIR}/{MANIFEST_FILENAME}") as manifest_file:
        manifest = Manifest.model_validate_json(manifest_file.read())

    assert manifest.short_name == "static_files_example"
    assert manifest.static_files["static/css/styles.css"].mime_type == "text/css"
    assert manifest.static_files["static/css/styles.css"].size > 0
    assert manifest.static_files["static/js/test.js"].mime_type == "text/javascript"
    assert manifest.static_files["static/js/test.js"].size > 0


def test_runs_pre_build_hook(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["build_hooks"] = {
        "pre": "mkdir -p static && touch static/my_custom_pre_build_hook",
    }
    with config_path.open("w") as f:
        yaml.dump(config, f)

    qpy_pkg_path = tmp_path / "package.qpy"
    with ZipPackageBuilder(qpy_pkg_path, PackageSource(source_path)) as builder:
        builder.write_package()

    with ZipFile(qpy_pkg_path) as zipfile:
        assert zipfile.getinfo(f"{DIST_DIR}/static/my_custom_pre_build_hook")


@pytest.mark.source_pkg("static-files")
def test_runs_post_build_hook(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["build_hooks"] = {"post": "rm js/test.js"}
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with ZipPackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
        builder.write_package()

    assert not (source_path / "js" / "test.js").exists()


@pytest.mark.parametrize("hook", ["pre", "post"])
def test_runs_build_hook_fails(hook: str, tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["build_hooks"] = {hook: "false"}
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with (
        ZipPackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder,
        pytest.raises(PackageBuildError) as exc,
    ):
        builder.write_package()

    assert exc.match(rf"{hook} hook\[0\] failed")


def test_skips_python_bytecode(tmp_path: Path, source_path: Path) -> None:
    # ensure we have bytecode files
    py_sources = source_path / "python" / "local" / "minimal_example"
    compileall.compile_dir(py_sources, quiet=1)
    assert next((py_sources / "__pycache__").glob("__init__*.pyc"))  # don't hardcode Python version

    qpy_pkg_path = tmp_path / "package.qpy"
    with ZipPackageBuilder(qpy_pkg_path, PackageSource(source_path)) as builder:
        builder.write_package()

    with ZipFile(qpy_pkg_path) as zipfile:
        assert not any(
            Path(info.filename).parts[-1] == "__pycache__" if info.is_dir() else info.filename.endswith(".pyc")
            for info in zipfile.infolist()
        )


@pytest.mark.parametrize("copy_sources", [True, False])
def test_copy_sources(copy_sources: bool, tmp_path: Path, source_path: Path) -> None:
    qpy_pkg_path = tmp_path / "package.qpy"

    with ZipPackageBuilder(qpy_pkg_path, PackageSource(source_path), copy_sources=copy_sources) as builder:
        builder.write_package()

    with ZipFile(qpy_pkg_path) as zipfile:
        filenames = [zipinfo.filename for zipinfo in zipfile.infolist()]
        assert (PACKAGE_CONFIG_FILENAME in filenames) == copy_sources
        assert (".gitignore" in filenames) == copy_sources
        assert ("python/local/minimal_example/__init__.py" in filenames) == copy_sources


def test_dir_package_builder(tmp_path: Path, source_path: Path) -> None:
    with DirPackageBuilder(PackageSource(source_path)) as builder:
        builder.write_package()

    dist_dir = source_path / DIST_DIR
    assert (dist_dir / MANIFEST_FILENAME).is_file()
    assert (dist_dir / "python" / "local" / "minimal_example" / "__init__.py").is_file()
    assert (dist_dir / "dependencies" / "site-packages" / "questionpy" / "__init__.py").is_file()


def test_dir_package_builder_clears_dist(tmp_path: Path, source_path: Path) -> None:
    dist_dir = source_path / DIST_DIR
    (dist_dir / "static").mkdir(parents=True)
    some_file_path = dist_dir / "static" / "some_file.txt"
    some_file_path.touch()

    with DirPackageBuilder(PackageSource(source_path)) as builder:
        builder.write_package()

    assert not some_file_path.exists()
