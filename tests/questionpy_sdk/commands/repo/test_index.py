#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands.repo.index import index

from .conftest import assert_same_structure, create_package


def test_index_no_arguments_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(index)
    assert result.exit_code != 0


def test_index_invalid_root_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(index, ["invalid"])
    assert result.exit_code != 0


def test_index_empty_directory(runner: CliRunner, cwd: Path) -> None:
    result = runner.invoke(index, ["."])

    assert result.exit_code == 0
    assert_same_structure(cwd, (cwd / "META.json", cwd / "PACKAGES.json.gz"))


def test_index_with_existing_meta_and_index(runner: CliRunner, cwd: Path) -> None:
    (cwd / "META.json").touch()
    (cwd / "PACKAGES.json.gz").touch()

    result = runner.invoke(index, ["."])

    assert result.exit_code == 0
    assert_same_structure(cwd, (cwd / "META.json", cwd / "PACKAGES.json.gz"))


def test_index_allows_packages_root(runner: CliRunner, cwd: Path) -> None:
    path, _ = create_package(cwd, "test")

    result = runner.invoke(index, ["."])

    assert result.exit_code == 0
    assert_same_structure(
        cwd,
        (
            cwd / "META.json",
            cwd / "PACKAGES.json.gz",
            path,
        ),
    )


@pytest.mark.parametrize("depth", [1, 2, 3, 9])
def test_index_allows_packages_in_subdirectories(depth: int, runner: CliRunner, cwd: Path) -> None:
    # Create subdirectories.
    directory = cwd
    for _ in range(depth):
        directory /= "subdirectory"
    directory.mkdir(parents=True)

    path, _ = create_package(directory, "test")

    result = runner.invoke(index, ["."])
    assert result.exit_code == 0
    assert_same_structure(cwd, (cwd / "META.json", cwd / "PACKAGES.json.gz", path))
