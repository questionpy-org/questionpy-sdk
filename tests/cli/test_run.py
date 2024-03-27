#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

from click.testing import CliRunner

from questionpy_sdk.commands.run import run
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME


def test_run_no_arguments(runner: CliRunner) -> None:
    result = runner.invoke(run)
    assert result.exit_code != 0
    assert "Error: Missing argument 'PACKAGE'." in result.stdout


def test_run_with_not_existing_package(runner: CliRunner) -> None:
    result = runner.invoke(run, ["package.qpy"])
    assert result.exit_code != 0
    assert "'package.qpy' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_non_zip_file(runner: CliRunner, cwd: Path) -> None:
    with open(cwd / "README.md", "w", encoding="utf-8") as f:
        f.write("Foo bar")
    result = runner.invoke(run, ["README.md"])
    assert result.exit_code != 0
    assert "'README.md' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_dir_without_config(runner: CliRunner, cwd: Path) -> None:
    (cwd / "tests").mkdir()
    result = runner.invoke(run, ["tests"])
    assert result.exit_code != 0
    assert f"The config 'tests/{PACKAGE_CONFIG_FILENAME}' does not exist" in result.stdout
