#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

# Stop pylint complaining about fixtures.
# pylint: disable=redefined-outer-name

import asyncio
import tempfile
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Callable

import pytest
from aiohttp import web
from selenium import webdriver

from questionpy_sdk.webserver.app import WebServer


@pytest.fixture(scope="function")
def sdk_web_server(request: pytest.FixtureRequest) -> Iterator[WebServer]:
    # We DON'T want state files to persist between tests, so we use a temp dir which is removed after each test.
    with tempfile.TemporaryDirectory() as state_storage_tempdir:
        yield WebServer(request.function.qpy_package_location, state_storage_path=Path(state_storage_tempdir))


@pytest.fixture
def port(aiohttp_unused_port: Callable) -> int:
    return aiohttp_unused_port()


@pytest.fixture
def url(port: int) -> str:
    return f"http://localhost:{port}"


@pytest.fixture
def driver() -> Iterator[webdriver.Chrome]:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as chrome_driver:
        yield chrome_driver


def start_runner(web_app: web.Application, unused_port: int) -> None:
    runner = web.AppRunner(web_app)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', unused_port)
    loop.run_until_complete(site.start())
    loop.run_forever()


@pytest.fixture
def start_runner_thread(sdk_web_server: WebServer, port: int) -> Iterator:
    app_thread = threading.Thread(target=start_runner, args=(sdk_web_server.web_app, port))
    app_thread.daemon = True  # Set the thread as a daemon to automatically stop when main thread exits
    app_thread.start()

    yield
