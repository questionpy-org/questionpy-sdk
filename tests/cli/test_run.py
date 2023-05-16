from click.testing import CliRunner

from questionpy_sdk.commands.run import run


def test_run_no_arguments() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(run)
        assert result.exit_code != 0
        assert "Error: Missing argument 'PACKAGE'." in result.stdout


def test_run_with_not_existing_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(run, ["package.qpy"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'PACKAGE': File 'package.qpy' does not exist." in result.stdout
