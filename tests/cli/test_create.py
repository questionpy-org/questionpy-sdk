#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from filecmp import dircmp
from pathlib import Path
from zipfile import ZipFile

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands.create import create
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.resources import EXAMPLE_PACKAGE


def packages_are_equal(directory_1: Path, directory_2: Path) -> bool:
    comparison = dircmp(directory_1, directory_2, ignore=[])
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    if comparison.diff_files and comparison.diff_files != [PACKAGE_CONFIG_FILENAME]:
        return False
    for sub_comparison in comparison.subdirs.values():
        if not packages_are_equal(Path(sub_comparison.left), Path(sub_comparison.right)):
            return False
    return True


def test_create_no_arguments(runner: CliRunner) -> None:
    result = runner.invoke(create)
    assert result.exit_code != 0
    assert "Error: Missing argument 'SHORT_NAME'." in result.stdout


def test_create_example_package(runner: CliRunner, cwd: Path) -> None:
    with ZipFile(EXAMPLE_PACKAGE) as zip_file:
        original = cwd / "original"
        original.mkdir()
        zip_file.extractall(original / "example")

    result = runner.invoke(create, ["example"])
    assert result.exit_code == 0
    assert (cwd / "example").exists()
    assert packages_are_equal(cwd / "example", original / "example")


def test_create_with_existing_path(runner: CliRunner, cwd: Path) -> None:
    (cwd / "short_name").mkdir()
    result = runner.invoke(create, ["short_name"])
    assert result.exit_code != 0
    assert "The path 'short_name' already exists." in result.stdout


def test_create_with_out_path(runner: CliRunner, cwd: Path) -> None:
    out_path = cwd / "out"
    result = runner.invoke(create, ["example", "--out", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()


@pytest.mark.parametrize("short_name", ["default", "a_name", "_name", "name_", "_name_", "_a_name_", "a" * 127])
def test_create_with_valid_short_name(short_name: str, runner: CliRunner, cwd: Path) -> None:
    result = runner.invoke(create, [short_name])
    assert result.exit_code == 0
    assert (cwd / short_name).exists()


@pytest.mark.parametrize(
    "short_name",
    [
        "",
        "notValid",
        "not_valid ",
        "not-valid",
        "not~valid",
        "not valid",
        "\u03c0",
        "a" * 128,
        "42",
        "def",
        "class",
        "global",
        "match",
        "_",
    ],
)
def test_create_with_invalid_short_name(short_name: str, runner: CliRunner) -> None:
    result = runner.invoke(create, [short_name])
    assert result.exit_code != 0
    assert "Error: Invalid value for 'SHORT_NAME': " in result.stdout


@pytest.mark.parametrize("namespace", ["default", "a_name", "_name", "name_", "_name_", "_a_name_", "a" * 127])
def test_create_with_valid_namespace(namespace: str, runner: CliRunner, cwd: Path) -> None:
    result = runner.invoke(create, ["short_name", "--namespace", namespace])
    assert result.exit_code == 0
    assert (cwd / "short_name").exists()


@pytest.mark.parametrize(
    "namespace",
    [
        "",
        "notValid",
        "not_valid ",
        "not-valid",
        "not~valid",
        "not valid",
        "\u03c0",
        "a" * 128,
        "42",
        "def",
        "class",
        "global",
        "match",
        "_",
    ],
)
def test_create_with_invalid_namespace(namespace: str, runner: CliRunner) -> None:
    result = runner.invoke(create, ["short_name", "--namespace", namespace])
    assert result.exit_code != 0
    assert "Error: Invalid value for '--namespace' / '-n': " in result.stdout
