#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import contextlib
import os
import signal
import sys
import tempfile
from asyncio.subprocess import PIPE, Process
from collections.abc import AsyncIterator, Iterable, Iterator
from pathlib import Path
from typing import Any

import aiohttp
import pytest
from click.testing import CliRunner, Result

default_ctx_obj = {"no_interaction": False}


@pytest.fixture
def isolated_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[CliRunner, Path]]:
    """Provides Click's `CliRunner` inside an isolated filesystem.

    Commands in Click potentially rely on parent context to be available. In a test environment the parent context
    doesn't run and need to be mocked. This fixture provides a default value for `Context.obj` which can be overridden
    on a per-test basis using the `obj` keyword parameter on `CliRunner.invoke`.

    Yields: A tuple containing the `CliRunner` instance `runner` and the path to the temporary directory `path`.

    See: https://click.palletsprojects.com/en/8.1.x/api/#click.Context.obj
    """
    runner = CliRunner()
    invoke_orig = runner.invoke
    cwd_orig = Path.cwd()

    def invoke(*args: Any, **kwargs: Any) -> Result:
        new_obj = (
            {**default_ctx_obj, **kwargs["obj"]}
            if "obj" in kwargs and isinstance(kwargs["obj"], dict)
            else default_ctx_obj
        )
        return invoke_orig(*args, **{"obj": new_obj, **kwargs})

    with monkeypatch.context() as mp:
        mp.setattr(runner, "invoke", invoke)
        os.chdir(tmp_path)
        try:
            yield runner, tmp_path
        finally:
            os.chdir(cwd_orig)


@pytest.fixture  # noqa: FURB118
def runner(isolated_runner: tuple[CliRunner, Path]) -> CliRunner:
    return isolated_runner[0]


@pytest.fixture  # noqa: FURB118
def cwd(isolated_runner: tuple[CliRunner, Path]) -> Path:
    return isolated_runner[1]


@pytest.fixture
async def client_session() -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession() as session:
        yield session


# can't test long-running processes with `CliRunner` (https://github.com/pallets/click/issues/2171)
@contextlib.asynccontextmanager
async def long_running_cmd(args: Iterable[str], timeout: float = 5) -> AsyncIterator[Process]:
    with tempfile.TemporaryDirectory("qpy-state-storage") as state_dir:
        try:
            popen_args = [sys.executable, "-m", "questionpy_sdk", "--", *args]
            proc = await asyncio.create_subprocess_exec(
                *popen_args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env={"QPY_STATE_STORAGE_PATH": state_dir}
            )

            def terminate() -> None:
                with contextlib.suppress(ProcessLookupError):
                    proc.send_signal(signal.SIGTERM)

            # ensure tests don't hang indefinitely
            async def terminate_after_timeout() -> None:
                await asyncio.sleep(timeout)
                terminate()

            kill_task = asyncio.create_task(terminate_after_timeout())
            yield proc

        finally:
            if kill_task:
                kill_task.cancel()
            terminate()
            await proc.wait()


async def assert_webserver_is_up(session: aiohttp.ClientSession, port: int) -> None:
    for _ in range(50):  # allow 5 sec to come up
        try:
            async with session.get(f"http://localhost:{port}/") as response:
                assert response.status == 200
                return
        except aiohttp.ClientConnectionError:
            await asyncio.sleep(0.1)

    pytest.fail("Webserver didn't come up")
