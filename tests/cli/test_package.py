#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import os
import subprocess
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pytest
import yaml
from click.testing import CliRunner

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_sdk.commands.package import package
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.models import PackageConfig
from questionpy_sdk.package._helper import create_normalized_filename
from questionpy_sdk.resources import EXAMPLE_PACKAGE


def create_config(source: Path) -> PackageConfig:
    """Creates a config in the given `source` directory."""
    config = PackageConfig(short_name="short_name", author="pytest", api_version="0.1", version="0.1.0")
    with (source / PACKAGE_CONFIG_FILENAME).open("w") as file:
        yaml.dump(config.model_dump(exclude={"type"}), file)
    return config


def create_source_directory(root: Path, directory_name: str) -> PackageConfig:
    """Creates a source directory with a config in the given `root` directory."""
    source = root / directory_name
    source_python = source / "python" / "local" / "short_name"
    source_python.mkdir(parents=True)
    (source_python / "__init__.py").touch()
    return create_config(source)


def test_package_with_example_package(runner: CliRunner, cwd: Path) -> None:
    with ZipFile(EXAMPLE_PACKAGE) as zip_file:
        zip_file.extractall(cwd)

    result = runner.invoke(package, [str(cwd)])

    assert result.exit_code == 0
    assert "Successfully created " in result.stdout


def test_package_no_arguments_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(package)

    assert result.exit_code != 0
    assert "Error: Missing argument 'SOURCE'." in result.stdout


def test_package_with_not_existing_source_path_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(package, ["source"])

    assert result.exit_code != 0
    assert "Error: Invalid value for 'SOURCE': Directory 'source' does not exist." in result.stdout


def test_package_with_file_as_source_path_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "source").touch()

    result = runner.invoke(package, ["source"])

    assert result.exit_code != 0
    assert "Error: Invalid value for 'SOURCE': Directory 'source' is a file." in result.stdout


def test_package_with_missing_config_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "source").mkdir()

    result = runner.invoke(package, ["source"])

    assert result.exit_code != 0
    assert f"Error: The config 'source/{PACKAGE_CONFIG_FILENAME}' does not exist." in result.stdout


def test_package_with_invalid_out_path_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "source").mkdir()

    result = runner.invoke(package, ["source", "--out", "out"])

    assert result.exit_code != 0
    assert "Error: Invalid value for '--out' / '-o': Packages need the extension '.qpy'." in result.stdout


def test_package_with_only_source(runner: CliRunner, cwd: Path) -> None:
    config = create_source_directory(cwd, "source")

    result = runner.invoke(package, ["source"])

    assert result.exit_code == 0
    assert Path(".", f"{create_normalized_filename(config)}").exists()


def test_package_creates_package_in_cwd(runner: CliRunner, cwd: Path) -> None:
    config = create_source_directory(cwd, "source")
    # Change current working directory to 'cwd'.
    cwd /= "cwd"
    cwd.mkdir()
    os.chdir(cwd)

    result = runner.invoke(package, ["../source"])

    assert result.exit_code == 0
    assert Path(".", create_normalized_filename(config)).exists()


def test_package_with_out_path(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")

    result = runner.invoke(package, ["source", "--out", "source.qpy"])

    assert result.exit_code == 0
    assert (cwd / "source.qpy").exists()


def test_package_with_not_existing_config_raises_error(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    (cwd / "source" / PACKAGE_CONFIG_FILENAME).unlink()

    result = runner.invoke(package, ["source"])

    assert result.exit_code != 0
    assert f"Error: The config 'source/{PACKAGE_CONFIG_FILENAME}' does not exist." in result.stdout


@pytest.mark.parametrize("prompt_input", ["n", "N", "\n", "not_y"])
def test_package_with_existing_file_and_not_overwriting(prompt_input: str, runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    (cwd / "source.qpy").touch()

    result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)

    assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
    assert "Aborted!" in result.stdout
    assert result.exit_code != 0


@pytest.mark.parametrize("prompt_input", ["y", "Y"])
def test_package_with_existing_file_and_overwriting(prompt_input: str, runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    (cwd / "source.qpy").touch()

    result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)

    assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
    assert "Successfully created 'source.qpy'." in result.stdout
    assert result.exit_code == 0


def test_package_with_no_interaction_and_existing_file_raises(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    (cwd / "source.qpy").touch()

    result = runner.invoke(package, ["source", "--out", "source.qpy"], obj={"no_interaction": True})

    assert "Output file 'source.qpy' exists" in result.stdout
    assert result.exit_code != 0


def test_package_with_force_and_existing_file(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    (cwd / "source.qpy").touch()

    result = runner.invoke(package, ["source", "--out", "source.qpy", "--force"])

    assert "Successfully created 'source.qpy'." in result.stdout
    assert result.exit_code == 0


def test_package_without_sources(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    result = runner.invoke(package, ["source", "--without-sources", "--out", "source.qpy"])

    assert result.exit_code == 0
    with ZipFile(cwd / "source.qpy") as qpy_file:
        filenames = [zipinfo.filename for zipinfo in qpy_file.infolist()]
        assert PACKAGE_CONFIG_FILENAME not in filenames
        assert "python/local/short_name/__init__.py" not in filenames


def test_package_with_dev(runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    result = runner.invoke(package, ["source", "--dev"])

    assert result.exit_code == 0
    assert (cwd / "source" / DIST_DIR).is_dir()
    assert (cwd / "source" / DIST_DIR / MANIFEST_FILENAME).is_file()
    assert (cwd / "source" / DIST_DIR / "python" / "local" / "short_name" / "__init__.py").is_file()


@pytest.mark.parametrize(
    ("params", "expected_msg"),
    [
        (("--out", "source.qpy", "--dev"), "The options --out and --dev are mutually exclusive."),
        (("--without-sources", "--dev"), "The options --without-sources and --dev are mutually exclusive."),
        (("--force", "--dev"), "The options --force and --dev are mutually exclusive."),
    ],
)
def test_mutually_exclusive_options(params: tuple[str], expected_msg: str, runner: CliRunner, cwd: Path) -> None:
    create_source_directory(cwd, "source")
    result = runner.invoke(package, [*params, "source"])

    assert expected_msg in result.stdout
    assert result.exit_code != 0


def test_installing_requirement_fails(runner: CliRunner, cwd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_run(*_: Any, **__: Any) -> None:
        raise subprocess.CalledProcessError(1, "", stderr=b"some pip error")

    with ZipFile(EXAMPLE_PACKAGE) as zip_file:
        zip_file.extractall(cwd)

    config_path = cwd / PACKAGE_CONFIG_FILENAME
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    config["requirements"] = ["attrs==23.2.0", "pytz==2024.1"]
    with config_path.open("w") as f:
        yaml.dump(config, f)

    with monkeypatch.context() as mp:
        mp.setattr(subprocess, "run", mock_run)
        result = runner.invoke(package, [str(cwd)])

    assert result.exit_code != 0
    assert "Error: Failed to build package: Failed to install requirements: some pip error" in result.stdout
