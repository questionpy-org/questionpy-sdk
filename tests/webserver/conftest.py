#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import tempfile
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from aiohttp import web
from lxml import etree
from selenium import webdriver

from questionpy_sdk.webserver.app import WebServer


@pytest.fixture
def sdk_web_server(request: pytest.FixtureRequest) -> Iterator[WebServer]:
    # We DON'T want state files to persist between tests, so we use a temp dir which is removed after each test.
    with tempfile.TemporaryDirectory() as state_storage_tempdir:
        yield WebServer(request.function.qpy_package_location, state_storage_path=Path(state_storage_tempdir))


@pytest.fixture
def port(unused_tcp_port_factory: Callable) -> int:
    return unused_tcp_port_factory()


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
    site = web.TCPSite(runner, "localhost", unused_port)
    loop.run_until_complete(site.start())
    loop.run_forever()


@pytest.fixture
def _start_runner_thread(sdk_web_server: WebServer, port: int) -> None:
    app_thread = threading.Thread(target=start_runner, args=(sdk_web_server.web_app, port))
    app_thread.daemon = True  # Set the thread as a daemon to automatically stop when main thread exits
    app_thread.start()


def normalize_element(element: etree._Element) -> etree._Element:
    """Recursively normalize an XML element by sorting attributes and normalizing whitespace."""
    if element.text:
        element.text = " ".join(element.text.split())
    if element.tail:
        element.tail = " ".join(element.tail.split())

    if element.attrib:
        attributes = sorted(element.attrib.items())
        element.attrib.clear()
        element.attrib.update(attributes)

    for child in element:
        normalize_element(child)

    return element


def compare_xhtml(xhtml1: str, xhtml2: str) -> bool:
    parser = etree.XMLParser(remove_blank_text=True)
    tree1 = etree.fromstring(xhtml1, parser)
    tree2 = etree.fromstring(xhtml2, parser)

    normalize_element(tree1)
    normalize_element(tree2)

    return etree.tostring(tree1, method="c14n") == etree.tostring(tree2, method="c14n")
