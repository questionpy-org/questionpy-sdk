#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest
from selenium import webdriver

from questionpy import Attempt, NeedsManualScoringError, Question
from questionpy_common.environment import PackageInitFunction
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.app import WebServer
from questionpy_server.worker.runtime.package_location import FunctionPackageLocation


@pytest.fixture
def sdk_web_server(tmp_path: Path, request: pytest.FixtureRequest, port: int) -> WebServer:
    # We DON'T want state files to persist between tests, so we use a temp dir which is removed after each test.
    return WebServer(request.function.qpy_package_location, state_storage_path=tmp_path, port=port)


@pytest.fixture
def url(port: int) -> str:
    return f"http://localhost:{port}"


@pytest.fixture
def driver() -> Iterator[webdriver.Chrome]:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as chrome_driver:
        yield chrome_driver


def start_runner(web_app: WebServer) -> None:
    asyncio.run(web_app.run_forever())


@pytest.fixture
def _start_runner_thread(sdk_web_server: WebServer) -> None:
    app_thread = threading.Thread(target=start_runner, args=(sdk_web_server,))
    app_thread.daemon = True  # Set the thread as a daemon to automatically stop when main thread exits
    app_thread.start()


_C = TypeVar("_C", bound=Callable)


def use_package(init_fun: PackageInitFunction, manifest: Manifest | None = None) -> Callable[[_C], _C]:
    def decorator(wrapped: _C) -> _C:
        cast(Any, wrapped).qpy_package_location = FunctionPackageLocation.from_function(init_fun, manifest)
        return wrapped

    return decorator


class _NoopAttempt(Attempt):
    def _compute_score(self) -> float:
        raise NeedsManualScoringError

    formulation = ""


class _NoopQuestion(Question):
    attempt_class = _NoopAttempt
