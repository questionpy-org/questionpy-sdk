#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import os
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml
from click.testing import CliRunner

from questionpy_sdk.commands._helper import create_normalized_filename
from questionpy_sdk.commands.package import package
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.models import PackageConfig
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
    source.mkdir()
    return create_config(source)


def test_package_with_example_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        with ZipFile(EXAMPLE_PACKAGE) as zip_file:
            zip_file.extractall(directory)
        result = runner.invoke(package, [directory])
        assert result.exit_code == 0
        assert "Successfully created " in result.stdout


def test_package_no_arguments_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(package)
        assert result.exit_code != 0
        assert "Error: Missing argument 'SOURCE'." in result.stdout


def test_package_with_not_existing_source_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(package, ["source"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'SOURCE': Directory 'source' does not exist." in result.stdout


def test_package_with_file_as_source_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "source").touch()
        result = runner.invoke(package, ["source"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'SOURCE': Directory 'source' is a file." in result.stdout


def test_package_with_missing_config_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "source").mkdir()
        result = runner.invoke(package, ["source"])
        assert result.exit_code != 0
        assert f"Error: The config 'source/{PACKAGE_CONFIG_FILENAME}' does not exist." in result.stdout


def test_package_with_invalid_out_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "source").mkdir()
        result = runner.invoke(package, ["source", "--out", "out"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--out' / '-o': Packages need the extension '.qpy'." in result.stdout


def test_package_with_only_source() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        config = create_source_directory(Path(fs), "source")
        result = runner.invoke(package, ["source"])
        assert result.exit_code == 0
        assert Path(".", f"{create_normalized_filename(config)}").exists()


def test_package_creates_package_in_cwd() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        config = create_source_directory(directory, "source")

        # Change current working directory to 'cwd'.
        cwd = Path(directory, "cwd")
        cwd.mkdir()
        os.chdir(cwd)

        result = runner.invoke(package, ["../source"])
        assert result.exit_code == 0
        assert Path(".", create_normalized_filename(config)).exists()


def test_package_with_out_path() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        create_source_directory(directory, "source")

        result = runner.invoke(package, ["source", "--out", "source.qpy"])
        assert result.exit_code == 0
        assert Path(directory, "source.qpy").exists()


def test_package_with_not_existing_config_as_argument_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        (directory / "config").mkdir()
        result = runner.invoke(package, ["source", "--config", "config.yml"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--config' / '-c': File 'config.yml' does not exist." in result.stdout


def test_package_with_directory_as_config_argument_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        (directory / "source").mkdir()
        (directory / "config.yml").mkdir()
        result = runner.invoke(package, ["source", "--config", "config.yml"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--config' / '-c': File 'config.yml' is a directory." in result.stdout


def test_package_with_invalid_yaml_as_config_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        (directory / "source").mkdir()
        (directory / "config.yml").write_text("{")

        result = runner.invoke(package, ["source", "--config", "config.yml"])
        assert result.exit_code != 0
        assert "Error: Failed to parse config 'config.yml': " in result.stdout


def test_package_with_invalid_config_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        (directory / "source").mkdir()
        (directory / "config.yml").write_text("invalid: config")

        result = runner.invoke(package, ["source", "--config", "config.yml"])
        assert result.exit_code != 0
        assert "Invalid config 'config.yml': " in result.stdout


def test_package_with_namespace_argument() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)

        # Create empty source directory and config in the root directory.
        (directory / "source").mkdir()
        config = create_config(directory)

        result = runner.invoke(package, ["source", "--config", PACKAGE_CONFIG_FILENAME])
        assert f"Successfully created '{create_normalized_filename(config)}'." in result.stdout
        assert result.exit_code == 0


@pytest.mark.parametrize("prompt_input", ["n", "N", "\n", "not_y"])
def test_package_with_existing_file_and_not_overwriting(prompt_input: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        create_source_directory(directory, "source")
        (directory / "source.qpy").touch()

        result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)
        assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
        assert "Aborted!" in result.stdout
        assert result.exit_code != 0


@pytest.mark.parametrize("prompt_input", ["y", "Y"])
def test_package_with_existing_file_and_overwriting(prompt_input: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        create_source_directory(directory, "source")
        (directory / "source.qpy").touch()

        result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)
        assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
        assert "Successfully created 'source.qpy'." in result.stdout
        assert result.exit_code == 0


# TODO: Implement or remove this test
@pytest.mark.skip(reason="Not implemented yet.")
def test_installing_requirement_fails() -> None:
    pass
