import os
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml
from click.testing import CliRunner

from questionpy_common.manifest import Manifest

from questionpy_sdk.commands.package import package
from questionpy_sdk.resources import EXAMPLE_PACKAGE
from tests.conftest import normalized_file_name


def create_manifest(source: Path) -> Manifest:
    """
    Creates a manifest in the given `source` directory.
    """
    manifest = Manifest(short_name="short_name", author="pytest", api_version="0.1", version="0.1.0")
    with (source / "qpy_manifest.yml").open("w") as file:
        yaml.dump(manifest.dict(exclude={"type"}), file)
    return manifest


def create_source_directory(root: Path, directory_name: str) -> Manifest:
    """
    Creates a source directory with a manifest in the given `root` directory.
    """
    source = root / directory_name
    source.mkdir()
    return create_manifest(source)


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


def test_package_with_missing_manifest_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "source").mkdir()
        result = runner.invoke(package, ["source"])
        assert result.exit_code != 0
        assert "Error: The manifest 'source/qpy_manifest.yml' does not exist." in result.stdout


def test_package_with_invalid_out_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "source").mkdir()
        result = runner.invoke(package, ["source", "--out", "out"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--out' / '-o': Packages need the extension '.qpy'." in result.stdout


def test_package_with_only_source() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        manifest = create_source_directory(Path(f), "source")
        result = runner.invoke(package, ["source"])
        assert result.exit_code == 0
        assert Path(".", f"{normalized_file_name(manifest)}").exists()


def test_package_creates_package_in_cwd() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        manifest = create_source_directory(directory, "source")

        # Change current working directory to 'cwd'.
        cwd = Path(directory, "cwd")
        cwd.mkdir()
        os.chdir(cwd)

        result = runner.invoke(package, ["../source"])
        assert result.exit_code == 0
        assert Path(".", normalized_file_name(manifest)).exists()


def test_package_with_out_path() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        create_source_directory(directory, "source")

        result = runner.invoke(package, ["source", "--out", "source.qpy"])
        assert result.exit_code == 0
        assert Path(directory, "source.qpy").exists()


def test_package_with_not_existing_manifest_as_argument_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        (directory / "source").mkdir()
        result = runner.invoke(package, ["source", "--manifest", "manifest.yml"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--manifest' / '-m': File 'manifest.yml' does not exist." in result.stdout


def test_package_with_directory_as_manifest_argument_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        (directory / "source").mkdir()
        (directory / "manifest.yml").mkdir()
        result = runner.invoke(package, ["source", "--manifest", "manifest.yml"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--manifest' / '-m': File 'manifest.yml' is a directory." in result.stdout


def test_package_with_invalid_yaml_as_manifest_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        (directory / "source").mkdir()
        (directory / "manifest.yml").write_text("{")

        result = runner.invoke(package, ["source", "--manifest", "manifest.yml"])
        assert result.exit_code != 0
        assert "Error: Failed to parse manifest 'manifest.yml': " in result.stdout


def test_package_with_invalid_manifest_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        (directory / "source").mkdir()
        (directory / "manifest.yml").write_text("invalid: manifest")

        result = runner.invoke(package, ["source", "--manifest", "manifest.yml"])
        assert result.exit_code != 0
        assert "Invalid manifest 'manifest.yml': " in result.stdout


def test_package_with_namespace_argument() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)

        # Create empty source directory and manifest in the root directory.
        (directory / "source").mkdir()
        manifest = create_manifest(directory)

        result = runner.invoke(package, ["source", "--manifest", "qpy_manifest.yml"])
        assert f"Successfully created '{normalized_file_name(manifest)}'." in result.stdout
        assert result.exit_code == 0


@pytest.mark.parametrize("prompt_input", ["n", "N", "\n", "not_y"])
def test_package_with_existing_file_and_not_overwriting(prompt_input: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        create_source_directory(directory, "source")
        (directory / "source.qpy").touch()

        result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)
        assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
        assert "Aborted!" in result.stdout
        assert result.exit_code != 0


@pytest.mark.parametrize("prompt_input", ["y", "Y"])
def test_package_with_existing_file_and_overwriting(prompt_input: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as f:
        directory = Path(f)
        create_source_directory(directory, "source")
        (directory / "source.qpy").touch()

        result = runner.invoke(package, ["source", "--out", "source.qpy"], input=prompt_input)
        assert "The path 'source.qpy' already exists. Do you want to overwrite it?" in result.stdout
        assert "Successfully created 'source.qpy'." in result.stdout
        assert result.exit_code == 0


@pytest.mark.skip(reason="Not implemented yet.")
def test_installing_requirement_fails() -> None:
    pass
