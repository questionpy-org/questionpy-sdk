#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import contextlib
import os
import signal
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

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


# can't test long-running processes with `CliRunner` (https://github.com/pallets/click/issues/2171)
@contextlib.contextmanager
def long_running_cmd(args: list[str]) -> Iterator[subprocess.Popen]:
    try:
        popen_args = [sys.executable, "-m", "questionpy_sdk", "--", *args]
        proc = subprocess.Popen(popen_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        yield proc
    finally:
        proc.send_signal(signal.SIGINT)
        proc.wait()
