#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

from click.testing import CliRunner

from questionpy_sdk.commands.run import run


def test_run_no_arguments(runner: CliRunner) -> None:
    result = runner.invoke(run)
    assert result.exit_code != 0
    assert "Error: Missing argument 'PACKAGE'." in result.stdout


def test_run_with_not_existing_package(runner: CliRunner) -> None:
    result = runner.invoke(run, ["package.qpy"])
    assert result.exit_code != 0
    assert "'package.qpy' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_non_zip_file(runner: CliRunner, cwd: Path) -> None:
    (cwd / "README.md").write_text("Foo bar")
    result = runner.invoke(run, ["README.md"])
    assert result.exit_code != 0
    assert "'README.md' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_dir_without_manifest(runner: CliRunner, cwd: Path) -> None:
    (cwd / "tests").mkdir()
    result = runner.invoke(run, ["tests"])
    assert result.exit_code != 0
    assert "Could not find package manifest" in result.stdout
