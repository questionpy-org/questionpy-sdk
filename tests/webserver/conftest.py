#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Callable
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
def package_and_manifest() -> Iterator[tuple[Path, Manifest]]:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        with ZipFile(EXAMPLE_PACKAGE) as zip_file:
            zip_file.extractall(directory)

        result = runner.invoke(package, [directory])
        if result.exit_code != 0:
            raise RuntimeError(result.stdout)

        root = Path(directory)
        package_files = list(root.glob('*.qpy'))
        if not package_files:
            raise FileNotFoundError("Error: No file with suffix \".qpy\" found.")

        manifest_files = list(root.glob('*.yml'))
        if not manifest_files:
            raise FileNotFoundError("Error: No file with suffix \".yml\" found.")

        with open(manifest_files[0], 'r', encoding='utf-8') as manifest_f:
            manifest_content = yaml.load(manifest_f, yaml.Loader)

        yield package_files[0], Manifest(**manifest_content)


@pytest.fixture
def test_package(package_and_manifest: tuple[Path, Manifest]) -> Iterator[Path]:
    package_path, _ = package_and_manifest
    yield package_path


@pytest.fixture
def manifest(package_and_manifest: tuple[Path, Manifest]) -> Iterator[Manifest]:
    _, test_manifest = package_and_manifest
    yield test_manifest


@pytest.fixture
def app(test_package: Path) -> web.Application:
    return WebServer(test_package).web_app


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
def start_runner_thread(app: web.Application, port: int) -> Iterator:
    app_thread = threading.Thread(target=start_runner, args=(app, port))
    app_thread.daemon = True  # Set the thread as a daemon to automatically stop when main thread exits
    app_thread.start()

    yield
