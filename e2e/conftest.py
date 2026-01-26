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
from questionpy_common.manifest import Bcp47LanguageTag
from questionpy_sdk.webserver.server import WebServer
from questionpy_server.worker.impl.thread import ThreadWorker
from questionpy_server.worker.runtime.package_location import FunctionPackageLocation

# Worker needs to be able to import init function from here
package_init_func: PackageInitFunction


@pytest.fixture
def url_path() -> str:
    return "/"


@pytest.fixture
def url(unused_tcp_port: int, url_path: str) -> str:
    return urljoin(f"http://localhost:{unused_tcp_port}/", url_path)


@pytest.fixture
def form_options() -> type[FormModel]:
    class PackageForm(FormModel):
        text_input: str = text_input("Text input", required=True)

    return PackageForm


@pytest.fixture
def attempt() -> type[Attempt]:
    class TestAttempt(Attempt):
        def _compute_score(self) -> float:
            raise NeedsManualScoringError

        formulation = (
            '<div xmlns="http://www.w3.org/1999/xhtml" xmlns:qpy="http://questionpy.org/ns/question">'
            "<p>Formulation text</p>"
            "</div>"
        )

    return TestAttempt


@pytest.fixture
def init_func(form_options: type[FormModel], attempt: type[Attempt]) -> PackageInitFunction:
    def _package_init_func(package: Package) -> QuestionTypeInterface:
        class PackageQuestion(Question):
            attempt_class = attempt

        # Set type annotation at runtime
        PackageQuestion.__annotations__["options"] = form_options

        return QuestionTypeWrapper(PackageQuestion, package)

    return _package_init_func


@pytest.fixture
def manifest(attempt: type[Attempt]) -> Manifest:
    # namespace/short_name need to match attempt module
    module_name = attempt.__module__
    namespace, short_name, *_ = module_name.split(".", maxsplit=2)

    return Manifest(
        short_name=short_name,
        namespace=namespace,
        version="0.1.0-test",
        api_version="0.1",
        author="Jane Doe",
        name={Bcp47LanguageTag("en"): "E2E Test Package"},
        languages=[Bcp47LanguageTag("en")],
    )


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
    global package_init_func  # noqa: PLW0603
    package_init_func = init_func

    async with WebServer(
        package_location=FunctionPackageLocation(__name__, "package_init_func", manifest),
        state_storage_path=tmp_path,
        port=unused_tcp_port,
        worker_class=ThreadWorker,  # SubprocessWorker wouldn't see dynamic package_init_func
    ):
        await page.goto(url)
        yield page
