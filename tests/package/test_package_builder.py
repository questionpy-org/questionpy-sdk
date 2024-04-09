#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
import yaml

from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.package.builder import PackageBuilder
from questionpy_sdk.package.errors import PackageBuildError
from questionpy_sdk.package.source import PackageSource


@pytest.fixture
def builder(tmp_path: Path, source_path: Path) -> Iterable[PackageBuilder]:
    with PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
        builder.write_package()
        yield builder


def test_installs_questionpy(builder: PackageBuilder) -> None:
    assert builder.getinfo("dependencies/site-packages/questionpy/__init__.py")


def test_installs_requirements_list(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["requirements"] = ["attrs==23.2.0", "pytz==2024.1"]
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
        builder.write_package()
        assert builder.getinfo("dependencies/site-packages/attrs/__init__.py")
        assert builder.getinfo("dependencies/site-packages/pytz/__init__.py")


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

    with PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
        builder.write_package()
        assert builder.getinfo("dependencies/site-packages/attrs/__init__.py")
        assert builder.getinfo("dependencies/site-packages/pytz/__init__.py")


def test_invalid_requirement_raises_error(source_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package_source = PackageSource(source_path)
    package_source.config.requirements = ["this_package_does_not_exist"]

    def mock_run(*_: Any, **__: Any) -> None:
        raise subprocess.CalledProcessError(1, "", stderr=b"some pip error")

    with monkeypatch.context() as mp:
        mp.setattr(subprocess, "run", mock_run)
        with (
            pytest.raises(PackageBuildError) as exc,
            PackageBuilder(tmp_path / "package.qpy", package_source) as builder,
        ):
            builder.write_package()

    assert exc.match("Failed to install requirements")


@pytest.mark.source_pkg("javascript")
def test_writes_package_files(builder: PackageBuilder) -> None:
    assert builder.getinfo("python/local/js_example/__init__.py")
    assert builder.getinfo("js/test.js")


def test_writes_manifest(builder: PackageBuilder) -> None:
    assert builder.getinfo("qpy_manifest.json")


def test_runs_pre_build_hook(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["build_hooks"] = {
        "pre": "mkdir -p static && touch static/my_custom_pre_build_hook",
    }
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
        builder.write_package()
        assert builder.getinfo("static/my_custom_pre_build_hook")


@pytest.mark.source_pkg("javascript")
def test_runs_post_build_hook(tmp_path: Path, source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["build_hooks"] = {"post": "rm js/test.js"}
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder:
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
        PackageBuilder(tmp_path / "package.qpy", PackageSource(source_path)) as builder,
        pytest.raises(PackageBuildError) as exc,
    ):
        builder.write_package()

    assert exc.match(rf"{hook} hook\[0\] failed")
