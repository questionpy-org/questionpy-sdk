#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import psutil
from aiohttp import ClientSession
from click.testing import CliRunner

from questionpy_common.constants import DIST_DIR, MANIFEST_FILENAME
from questionpy_sdk._package import ZipBuildTarget, build_qpy_package
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.commands.run import run
from tests.questionpy_sdk.commands.conftest import assert_webserver_is_up, long_running_cmd


def test_run_no_arguments(runner: CliRunner) -> None:
    result = runner.invoke(run)
    assert result.exit_code != 0
    assert "Error: Missing argument 'PACKAGE'." in result.output


def test_run_with_not_existing_package(runner: CliRunner) -> None:
    result = runner.invoke(run, ["package.qpy"])
    assert result.exit_code != 0
    assert "'package.qpy' doesn't look like a QPy package file, source directory, or dist directory." in result.output


def test_run_non_zip_file(runner: CliRunner, cwd: Path) -> None:
    (cwd / "README.md").write_text("Foo bar")
    result = runner.invoke(run, ["README.md"])
    assert result.exit_code != 0
    assert "'README.md' doesn't look like a QPy package file, source directory, or dist directory." in result.output


async def test_run_source_dir_builds_package(source_path: Path, client_session: ClientSession, port: int) -> None:
    async with long_running_cmd(("run", "--port", str(port), str(source_path))) as proc:
        assert proc.stdout
        first_line = (await proc.stdout.readline()).decode("utf-8")
        assert f"Successfully built package '{source_path}'" in first_line
        assert (source_path / DIST_DIR / MANIFEST_FILENAME).exists()
        await assert_webserver_is_up(client_session, port)


async def test_run_dist_dir(source_path: Path, client_session: ClientSession, port: int) -> None:
    build_qpy_package(PackageSource(source_path))

    async with long_running_cmd(("run", "--port", str(port), str(source_path / DIST_DIR))):
        await assert_webserver_is_up(client_session, port)


async def test_run_watch_with_source_dir(source_path: Path, client_session: ClientSession, port: int) -> None:
    async with long_running_cmd(("run", "--watch", "--port", str(port), str(source_path))):
        await assert_webserver_is_up(client_session, port)


async def test_run_watch_with_dist_dir(source_path: Path, port: int) -> None:
    build_qpy_package(PackageSource(source_path))

    async with long_running_cmd(("run", "--watch", "--port", str(port), str(source_path / DIST_DIR))) as proc:
        assert proc.stderr
        assert await proc.wait() != 0
        stderr = (await proc.stderr.read()).decode("utf-8")
        assert "The --watch option only works with source directories." in stderr


async def test_run_watch_with_qpy_file(cwd: Path, source_path: Path, port: int) -> None:
    qpy_path = cwd / "test.qpy"
    build_qpy_package(PackageSource(source_path), ZipBuildTarget(qpy_path))

    async with long_running_cmd(("run", "--watch", "--port", str(port), str(qpy_path))) as proc:
        assert proc.stderr
        assert await proc.wait() != 0
        stderr = (await proc.stderr.read()).decode("utf-8")
        assert "The --watch option only works with source directories." in stderr


async def test_run_explicit_subprocess_worker_with_qpy_file(
    source_path: Path, client_session: ClientSession, port: int
) -> None:
    async with long_running_cmd(("run", "-Wsubprocess", "--port", str(port), str(source_path))) as proc:
        await assert_webserver_is_up(client_session, port)

        assert len(psutil.Process(proc.pid).children()) == 1


async def test_run_explicit_thread_worker_with_qpy_file(
    source_path: Path, client_session: ClientSession, port: int
) -> None:
    async with long_running_cmd(("run", "-Wthread", "--port", str(port), str(source_path))) as proc:
        await assert_webserver_is_up(client_session, port)

        assert len(psutil.Process(proc.pid).children()) == 0
        # Python doesn't call pthread_setname_np, so we have no way of getting the thread names of subprocess to check
        # for the existence of worker threads.
