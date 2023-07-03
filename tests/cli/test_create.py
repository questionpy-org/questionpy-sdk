#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from filecmp import dircmp
from zipfile import ZipFile

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands.create import create
from questionpy_sdk.resources import EXAMPLE_PACKAGE


def packages_are_equal(directory_1: Path, directory_2: Path) -> bool:
    comparison = dircmp(directory_1, directory_2, ignore=[])
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    if comparison.diff_files and comparison.diff_files != ["qpy_manifest.yml"]:
        return False
    for sub_comparison in comparison.subdirs.values():
        if not packages_are_equal(Path(sub_comparison.left), Path(sub_comparison.right)):
            return False
    return True


def test_create_no_arguments() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(create)
        assert result.exit_code != 0
        assert "Error: Missing argument 'SHORT_NAME'." in result.stdout


def test_create_example_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs)
        with ZipFile(EXAMPLE_PACKAGE) as zip_file:
            original = directory / "original"
            original.mkdir()
            zip_file.extractall(original / "example")

        result = runner.invoke(create, ["example"])
        assert result.exit_code == 0
        assert (directory / "example").exists()
        assert packages_are_equal(directory / "example", original / "example")


def test_create_with_existing_path() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "short_name").mkdir()
        result = runner.invoke(create, ["short_name"])
        assert result.exit_code != 0
        assert "The path 'short_name' already exists." in result.stdout


def test_create_with_out_path() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        out_path = Path(directory, "out")
        result = runner.invoke(create, ["example", "--out", str(out_path)])
        assert result.exit_code == 0
        assert out_path.exists()


@pytest.mark.parametrize("short_name", [
    "default",
    "a_name",
    "_name",
    "name_",
    "_name_",
    "_a_name_",
    "a" * 127
])
def test_create_with_valid_short_name(short_name: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        result = runner.invoke(create, [short_name])
        assert result.exit_code == 0
        assert Path(directory, short_name).exists()


@pytest.mark.parametrize("short_name", [
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
    "_"
])
def test_create_with_invalid_short_name(short_name: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(create, [short_name])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'SHORT_NAME': " in result.stdout


@pytest.mark.parametrize("namespace", [
    "default",
    "a_name",
    "_name",
    "name_",
    "_name_",
    "_a_name_",
    "a" * 127
])
def test_create_with_valid_namespace(namespace: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        result = runner.invoke(create, ["short_name", "--namespace", namespace])
        assert result.exit_code == 0
        assert Path(directory, "short_name").exists()


@pytest.mark.parametrize("namespace", [
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
    "_"
])
def test_create_with_invalid_namespace(namespace: str) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(create, ["short_name", "--namespace", namespace])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--namespace' / '-n': " in result.stdout
