#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urljoin

import pytest
from playwright.async_api import Page

from questionpy import Attempt, Manifest, NeedsManualScoringError, Package, Question, QuestionTypeWrapper
from questionpy.form import FormModel, text_input
from questionpy_common.api.qtype import QuestionTypeInterface
from questionpy_common.environment import PackageInitFunction
from questionpy_sdk.webserver.app import WebServer
from questionpy_server.worker.runtime.package_location import FunctionPackageLocation


@pytest.fixture
def url_path() -> str:
    return "/"


@pytest.fixture
def url(unused_tcp_port: int, url_path: str) -> str:
    return urljoin(f"http://localhost:{unused_tcp_port}/", url_path)


def default_init(package: Package) -> QuestionTypeInterface:
    class PackageForm(FormModel):
        text_input: str = text_input("Static text label", required=True)

    class TestAttempt(Attempt):
        def _compute_score(self) -> float:
            raise NeedsManualScoringError

        formulation = (
            '<div xmlns="http://www.w3.org/1999/xhtml" xmlns:qpy="http://questionpy.org/ns/question">'
            "<p>Formulation text</p>"
            "</div>"
        )

    class PackageQuestion(Question):
        attempt_class = TestAttempt
        options: PackageForm

    return QuestionTypeWrapper(PackageQuestion, package)


@pytest.fixture
def init_func() -> PackageInitFunction:
    return default_init


@pytest.fixture
def manifest() -> Manifest | None:
    return None


@pytest.fixture
async def page(
    page: Page,
    tmp_path: Path,
    unused_tcp_port: int,
    url: str,
    init_func: PackageInitFunction,
    manifest: Manifest | None,
) -> AsyncIterator[Page]:
    """Overrides pytest-playwright-asyncio's `page` fixture to include setup/teardown for the SDK web server."""
    pkg_location = FunctionPackageLocation.from_function(init_func, manifest)
    async with WebServer(pkg_location, state_storage_path=tmp_path, port=unused_tcp_port):
        await page.goto(url)
        yield page
