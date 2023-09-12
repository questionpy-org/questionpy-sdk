#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import threading
from pathlib import Path
from typing import Generator, Callable
from zipfile import ZipFile

import pytest
import yaml
from aiohttp import web
from click.testing import CliRunner
from questionpy_common.manifest import Manifest
from selenium import webdriver

from questionpy_sdk.commands.package import package
from questionpy_sdk.resources import EXAMPLE_PACKAGE
from questionpy_sdk.webserver.app import WebServer


@pytest.fixture
def package_and_manifest() -> Generator[tuple[Path, Manifest], None, None]:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        with ZipFile(EXAMPLE_PACKAGE) as zip_file:
            zip_file.extractall(directory)
        result = runner.invoke(package, [directory])
        if result.exit_code != 0:
            raise RuntimeError(result.stdout)
        root = Path(directory)
        package_list = [f for f in root.iterdir() if f.suffix == '.qpy']
        if not package_list:
            raise FileNotFoundError("Error: No file with suffix \".qpy\" found.")
        test_package = next(iter(package_list))
        manifest_list = [f for f in root.iterdir() if f.suffix == '.yml']
        if not package_list:
            raise FileNotFoundError("Error: No file with suffix \".yml\" found.")
        with open(next(iter(manifest_list)), 'r') as manifest_f:
            manifest = yaml.load(manifest_f, yaml.Loader)

        yield test_package, Manifest(**manifest)


@pytest.fixture
def test_package(package_and_manifest: tuple[Path, Manifest]) -> Generator[Path, None, None]:
    test_package, _ = package_and_manifest
    yield test_package


@pytest.fixture
def manifest(package_and_manifest: tuple[Path, Manifest]) -> Generator[Manifest, None, None]:
    _, manifest = package_and_manifest
    yield manifest


@pytest.fixture
def app(test_package: Path) -> web.Application:
    return WebServer(test_package).web_app


@pytest.fixture
def port(aiohttp_unused_port: Callable) -> int:
    return aiohttp_unused_port()


@pytest.fixture
def url(port: int) -> str:
    return "http://localhost:{}".format(port)


@pytest.fixture
def driver() -> Generator[webdriver.Chrome, None, None]:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as driver:
        yield driver


def start_runner(app: web.Application, port: int) -> None:
    runner = web.AppRunner(app)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', port)  # Change to your desired host and port
    loop.run_until_complete(site.start())
    loop.run_forever()


@pytest.fixture
def start_runner_thread(app: web.Application, port: int) -> Generator[None, None, None]:
    app_thread = threading.Thread(target=start_runner, args=(app, port))
    app_thread.daemon = True  # Set the thread as a daemon to automatically stop when main thread exits
    app_thread.start()

    yield
