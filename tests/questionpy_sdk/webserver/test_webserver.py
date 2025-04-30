#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
from pathlib import Path

import pytest

from questionpy import Attempt, NeedsManualScoringError, Package, Question, QuestionTypeWrapper
from questionpy.form import FormModel
from questionpy_common.api.qtype import QuestionTypeInterface
from questionpy_common.constants import DIST_DIR
from questionpy_sdk.package.builder import DirPackageBuilder
from questionpy_sdk.package.source import PackageSource
from questionpy_sdk.webserver.server import WebServer
from questionpy_server.hash import calculate_hash
from questionpy_server.worker.runtime.package_location import (
    DirPackageLocation,
    FunctionPackageLocation,
    ZipPackageLocation,
)


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


async def _assert_graceful_shutdown(webserver: WebServer) -> None:
    await webserver.start_server()
    await webserver.stop_server()

    # give loop a moment to settle
    await asyncio.sleep(0)

    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    if pending:
        pending_tasks_display = "\n".join(f"  - {t}" for t in pending)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        pytest.fail(f"Pending tasks after shutdown:\n{pending_tasks_display}")


@pytest.mark.asyncio(loop_scope="function")
async def test_webserver_shutdown_function(tmp_path: Path, port: int) -> None:
    pkg_location = FunctionPackageLocation.from_function(_pkg_init)
    webserver = WebServer(pkg_location, state_storage_path=tmp_path, port=port)

    await _assert_graceful_shutdown(webserver)


@pytest.mark.asyncio(loop_scope="function")
async def test_webserver_shutdown_dir(tmp_path: Path, port: int, source_path: Path) -> None:
    with DirPackageBuilder(PackageSource(source_path)) as builder:
        builder.write_package()
    pkg_location = DirPackageLocation(source_path / DIST_DIR)
    webserver = WebServer(pkg_location, state_storage_path=tmp_path, port=port)

    await _assert_graceful_shutdown(webserver)


@pytest.mark.asyncio(loop_scope="function")
async def test_webserver_shutdown_zip(tmp_path: Path, port: int, qpy_pkg_path: Path) -> None:
    pkg_location = ZipPackageLocation(qpy_pkg_path, calculate_hash(qpy_pkg_path))
    webserver = WebServer(pkg_location, state_storage_path=tmp_path, port=port)

    await _assert_graceful_shutdown(webserver)
