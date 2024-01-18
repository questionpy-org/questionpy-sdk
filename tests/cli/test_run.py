#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from click.testing import CliRunner

from questionpy_sdk.commands.run import run


def test_run_no_arguments() -> None:
    runner = CliRunner()
    result = runner.invoke(run)
    assert result.exit_code != 0
    assert "Error: Missing argument 'PACKAGE'." in result.stdout


def test_run_with_not_existing_package() -> None:
    runner = CliRunner()
    result = runner.invoke(run, ["package.qpy"])
    assert result.exit_code != 0
    assert "'package.qpy' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_non_zip_file() -> None:
    runner = CliRunner()
    result = runner.invoke(run, ["README.md"])
    assert result.exit_code != 0
    assert "'README.md' doesn't look like a QPy package zip file, directory or module" in result.stdout


def test_run_dir_without_manifest() -> None:
    runner = CliRunner()
    result = runner.invoke(run, ["tests"])
    assert result.exit_code != 0
    assert "The manifest 'tests/qpy_manifest.yml' does not exist" in result.stdout
