from pathlib import Path

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands.repo.index import index
from tests.conftest import assert_same_structure, create_package


def test_index_no_arguments_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(index)
        assert result.exit_code != 0


def test_index_invalid_root_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(index, ["invalid"])
        assert result.exit_code != 0


def test_index_empty_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()

        result = runner.invoke(index, ["."])
        assert result.exit_code == 0
        assert_same_structure(cwd, [
            cwd / 'META.json',
            cwd / 'PACKAGES.json.gz'
        ])


def test_index_with_existing_meta_and_index() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        (cwd / "META.json").touch()
        (cwd / "PACKAGES.json.gz").touch()

        result = runner.invoke(index, ["."])
        assert result.exit_code == 0
        assert_same_structure(cwd, [
            cwd / 'META.json',
            cwd / 'PACKAGES.json.gz'
        ])


def test_index_allows_packages_root() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()

        path, _ = create_package(cwd, "test")

        result = runner.invoke(index, ["."])
        assert result.exit_code == 0
        assert_same_structure(cwd, [
            cwd / 'META.json',
            cwd / 'PACKAGES.json.gz',
            path
        ])


@pytest.mark.parametrize("depth", [1, 2, 3, 9])
def test_index_allows_packages_in_subdirectories(depth: int) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()

        # Create subdirectories.
        directory = cwd
        for _ in range(depth):
            directory = cwd / "subdirectory"
        directory.mkdir(parents=True)

        path, _ = create_package(directory, "test")

        result = runner.invoke(index, ["."])
        assert result.exit_code == 0
        assert_same_structure(cwd, [
            cwd / 'META.json',
            cwd / 'PACKAGES.json.gz',
            path
        ])
