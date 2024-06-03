#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

from click.testing import CliRunner

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_sdk.commands.run import run
from tests.cli.conftest import long_running_cmd


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


def test_run_dir_builds_package(source_path: Path) -> None:
    with long_running_cmd(["run", str(source_path)]) as proc:
        assert proc.stdout
        first_line = proc.stdout.readline().decode("utf-8")
        assert f"Successfully built package '{source_path}'" in first_line
        assert (source_path / DIST_DIR / MANIFEST_FILENAME).exists()
