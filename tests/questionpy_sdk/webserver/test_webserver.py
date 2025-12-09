#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from aiohttp import web

from questionpy import Attempt, NeedsManualScoringError, Package, Question, QuestionTypeWrapper
from questionpy.form import FormModel
from questionpy_common.api.qtype import QuestionTypeInterface
from questionpy_common.constants import DIST_DIR
from questionpy_common.package_location import (
    DirPackageLocation,
    FunctionPackageLocation,
    PackageLocation,
    ZipPackageLocation,
)
from questionpy_sdk._package import build_qpy_package
from questionpy_sdk._package._helper import create_normalized_filename
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.webserver.server import WebServer
from questionpy_server.hash import calculate_hash


@pytest.fixture
def mock_state_manager(monkeypatch: pytest.MonkeyPatch) -> Iterator[Mock]:
    with monkeypatch.context() as mp:
        mock_state_manager_cls = Mock()
        mp.setattr("questionpy_sdk.webserver.server.FilesystemStateManager", mock_state_manager_cls)
        yield mock_state_manager_cls


async def test_webserver_startup(
    mock_worker_pool: tuple[Mock, MagicMock],
    mock_worker: AsyncMock,
    mock_web_components: tuple[Mock, AsyncMock],
    mock_state_manager: Mock,
) -> None:
    mock_worker_pool_cls, mock_worker_pool_instance = mock_worker_pool
    mock_app_runner, mock_tcp_site = mock_web_components

    package_location = FunctionPackageLocation("test")
    state_storage_path = Path("/tmp/storage")

    async with WebServer(package_location=package_location, state_storage_path=state_storage_path):
        mock_worker_pool_cls.assert_called_once()

        mock_worker_pool_instance.get_worker.assert_not_called()

        file_name = create_normalized_filename(package_location.manifest)
        expected_path = state_storage_path / file_name
        mock_state_manager.assert_called_once_with(expected_path.with_suffix(""))

        mock_app_runner.setup.assert_awaited_once()
        mock_tcp_site.return_value.start.assert_awaited_once()


async def test_webserver_shutdown(
    mock_worker_pool: tuple[Mock, MagicMock], mock_web_components: tuple[Mock, AsyncMock]
) -> None:
    _, mock_worker_pool_instance = mock_worker_pool
    mock_app_runner, _ = mock_web_components

    location = FunctionPackageLocation("test")
    async with WebServer(package_location=location, state_storage_path=Path("/tmp")):
        pass

    mock_app_runner.cleanup.assert_awaited_once()
    mock_worker_pool_instance.__aexit__.assert_awaited_once()


def test_create_webapp_frontend_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as mp:
        mp.setattr("questionpy_sdk.webserver.server.USE_VITE_DEV_SERVER", False)

        routes = web.RouteTableDef()

        @routes.get("/")
        async def some_route(r: web.Request) -> web.Response:  # noqa: RUF029
            return web.Response()

        mp.setattr("questionpy_sdk.webserver.server.frontend_routes", routes)

        server = WebServer(package_location=Mock(), state_storage_path=Path("/tmp"))
        app = server._create_webapp()

        assert some_route in (route.handler for route in app.router.routes())


def test_create_webapp_vite_middleware(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as mp:
        mp.setattr("questionpy_sdk.webserver.server.USE_VITE_DEV_SERVER", True)
        mock_middleware = Mock()
        mp.setattr("questionpy_sdk.webserver.middlewares.vite_dev.vite_devserver_middleware", mock_middleware)

        server = WebServer(package_location=Mock(), state_storage_path=Path("/tmp"))
        app = server._create_webapp()

        assert mock_middleware in app.middlewares


def test_print_status_logs_urls(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        server = WebServer(package_location=Mock(), state_storage_path=Path("/tmp"))
        server._runner = Mock()
        server._runner.addresses = [("127.0.0.1", 8080), ("::1", 8080, 0, 0)]

        server._print_status()

        assert "http://127.0.0.1:8080" in caplog.text
        assert "http://[::1]:8080" in caplog.text


def test_print_status_raises_on_invalid_address() -> None:
    server = WebServer(package_location=Mock(), state_storage_path=Path("/tmp"))
    server._runner = Mock()
    server._runner.addresses = [("invalid",)]

    with pytest.raises(ValueError, match="Unknown address format"):
        server._print_status()


def _pkg_init(package: Package) -> QuestionTypeInterface:
    class PackageForm(FormModel):
        pass

    class NoopAttempt(Attempt):
        def _compute_score(self) -> float:
            raise NeedsManualScoringError

        formulation = ""

    class PackageQuestion(Question):
        attempt_class = NoopAttempt
        options: PackageForm

    return QuestionTypeWrapper(PackageQuestion, package)


@pytest.fixture
def function_pkg_location() -> FunctionPackageLocation:
    return FunctionPackageLocation.from_function(_pkg_init)


@pytest.fixture
def dir_pkg_location(source_path: Path) -> DirPackageLocation:
    build_qpy_package(PackageSource(source_path))

    return DirPackageLocation(source_path / DIST_DIR)


@pytest.fixture
def zip_pkg_location(qpy_pkg_path: Path) -> ZipPackageLocation:
    return ZipPackageLocation(qpy_pkg_path, calculate_hash(qpy_pkg_path))


@pytest.fixture(params=["function_pkg_location", "dir_pkg_location", "zip_pkg_location"])
def pkg_location(request: pytest.FixtureRequest) -> PackageLocation:
    return request.getfixturevalue(request.param)


@pytest.mark.asyncio(loop_scope="function")
async def test_webserver_graceful_shutdown(pkg_location: PackageLocation, tmp_path: Path, port: int) -> None:
    async with WebServer(package_location=pkg_location, state_storage_path=tmp_path, port=port):
        await asyncio.sleep(0)

    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    if pending:
        pending_tasks_display = "\n".join(f"  - {t}" for t in pending)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        pytest.fail(f"Pending tasks after shutdown:\n{pending_tasks_display}")
