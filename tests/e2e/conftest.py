#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import sys
import threading
import warnings
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest
from selenium import webdriver

from questionpy import Attempt, NeedsManualScoringError, Question
from questionpy_common.environment import PackageInitFunction
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver_legacy.app import WebServer
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
    async def _run() -> None:
        async with web_app:
            await asyncio.Event().wait()

    asyncio.run(_run())


@pytest.fixture
def _webserver_thread(sdk_web_server: WebServer) -> Iterator[None]:
    loop = asyncio.new_event_loop()
    app_thread = threading.Thread(
        target=loop.run_forever,
        name="SDK WebServer under test",
        # Set the thread as a daemon to automatically stop when main thread exits
        daemon=True,
    )
    app_thread.start()

    asyncio.run_coroutine_threadsafe(sdk_web_server.__aenter__(), loop).result()  # noqa: PLC2801 (manual __aenter__)

    try:
        yield
    finally:
        asyncio.run_coroutine_threadsafe(sdk_web_server.__aexit__(*sys.exc_info()), loop).result()
        loop.call_soon_threadsafe(loop.stop)

        # After stopping the loop, loop.run_forever should return or raise, causing the thread to end.
        app_thread.join(2)
        if app_thread.is_alive():
            # If it doesn't, the loop and server probably won't be cleaned up, and that's a problem.
            warnings.warn("WebServer thread for E2E tests did not end gracefully.", stacklevel=1)

        loop.close()


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
