#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
from collections.abc import AsyncIterable, Iterable
from itertools import product
from pathlib import Path
from typing import NamedTuple, cast
from unittest.mock import AsyncMock, MagicMock, Mock, create_autospec

import pytest
from watchdog import events as we

from questionpy_sdk.package import build_qpy_package
from questionpy_sdk.package.errors import PackageBuildError
from questionpy_sdk.package.source import PackageSource
from questionpy_sdk.watcher import Watcher, _EventHandler
from questionpy_server.worker.runtime.messages import WorkerUnknownError

some_path = Path("/", "path", "to")


@pytest.fixture
def event_handler() -> _EventHandler:
    mock_loop = cast("asyncio.AbstractEventLoop", None)

    def ignore_path(path: Path) -> bool:
        return bool(path.parts and path.parts[0] == "ignopath")

    return _EventHandler(mock_loop, lambda: None, some_path, ignore_path)


@pytest.mark.parametrize(
    "event",
    [
        we.FileCreatedEvent(src_path=str(some_path / "foo")),
        we.FileCreatedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        we.FileDeletedEvent(src_path=str(some_path / "foo")),
        we.FileDeletedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        we.FileModifiedEvent(src_path=str(some_path)),
        we.FileModifiedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        we.FileMovedEvent(src_path=str(some_path / "ignopath" / "foo"), dest_path=str(some_path / "foo")),
        we.FileMovedEvent(src_path=str(some_path / "foo"), dest_path=str(some_path / "ignopath" / "foo")),
        we.FileMovedEvent(src_path=str(some_path / "foo"), dest_path=str(some_path / "bar")),
    ],
)
def test_event_handler_should_not_ignore(event: we.FileSystemEvent, event_handler: _EventHandler) -> None:
    assert not event_handler._ignore_event(event)


@pytest.mark.parametrize(
    "event",
    [
        we.FileClosedEvent(src_path=str(some_path / "foo")),
        we.FileCreatedEvent(src_path=str(some_path / "ignopath" / "foo")),
        we.FileDeletedEvent(src_path=str(some_path / "ignopath" / "foo")),
        we.FileModifiedEvent(src_path=str(some_path / "ignopath")),
        we.FileOpenedEvent(src_path=str(some_path / "foo")),
        we.FileMovedEvent(src_path=str(some_path / "ignopath" / "foo"), dest_path=str(some_path / "ignopath" / "bar")),
    ],
)
def test_event_handler_should_ignore(event: we.FileSystemEvent, event_handler: _EventHandler) -> None:
    assert event_handler._ignore_event(event)


@pytest.mark.parametrize(
    "event",
    [
        we.DirCreatedEvent(src_path=str(some_path / "foo")),
        we.DirDeletedEvent(src_path=str(some_path / "foo")),
        we.DirModifiedEvent(src_path=str(some_path / "foo")),
        we.DirMovedEvent(src_path=str(some_path / "ignopath" / "foo"), dest_path=str(some_path / "foo")),
    ],
)
def test_event_handler_should_ignore_dirs(event: we.FileSystemEvent, event_handler: _EventHandler) -> None:
    assert event_handler._ignore_event(event)


class WatchMockSetup(NamedTuple):
    observer_mock: Mock
    event_handler_mock: Mock
    webserver_mock: AsyncMock
    build_qpy_package_mock: MagicMock


@pytest.fixture
def watcher_mock_setup(monkeypatch: pytest.MonkeyPatch) -> Iterable[WatchMockSetup]:
    with monkeypatch.context() as mp:
        observer_mock = Mock()
        event_handler_mock = Mock()
        webserver_mock = AsyncMock()
        package_source_mock = MagicMock(spec=PackageSource)
        ignore_mock = MagicMock()
        ignore_mock.iter.return_value = iter([])
        package_source_mock.config.ignore = ignore_mock
        build_qpy_package_mock = create_autospec(build_qpy_package)
        mp.setattr("questionpy_sdk.watcher.Observer", Mock(return_value=observer_mock))
        mp.setattr("questionpy_sdk.watcher._EventHandler", Mock(return_value=event_handler_mock))
        mp.setattr("questionpy_sdk.watcher.WebServer", Mock(return_value=webserver_mock))
        mp.setattr("questionpy_sdk.watcher.PackageSource", Mock(return_value=package_source_mock))
        mp.setattr("questionpy_sdk.watcher.build_qpy_package", build_qpy_package_mock)

        yield WatchMockSetup(observer_mock, event_handler_mock, webserver_mock, build_qpy_package_mock)


@pytest.fixture
async def watcher(watcher_mock_setup: WatchMockSetup) -> AsyncIterable[Watcher]:
    async with Watcher(
        Path("source"), package_location=Mock(), state_storage_path=Path("storage"), host="localhost", port=1234
    ) as watcher:
        try:
            task = asyncio.create_task(watcher.run_forever())
            await asyncio.sleep(0)
            yield watcher
        finally:
            if not task.done():
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task


async def test_watcher_lifecycle(watcher_mock_setup: WatchMockSetup) -> None:
    observer_mock, event_handler_mock, _, _ = watcher_mock_setup

    async with Watcher(Path("source"), package_location=Mock(), state_storage_path=Path("/tmp")):
        observer_mock.start.assert_called_once()
        event_handler_mock.start.assert_called_once()

    observer_mock.stop.assert_called_once()
    event_handler_mock.stop.assert_called_once()


@pytest.mark.parametrize(
    ("server_crash", "build_error"),
    # Combinations of boolean value pairs
    product((False, True), repeat=2),
)
async def test_watcher_run_loop(
    server_crash: bool, build_error: bool, watcher_mock_setup: WatchMockSetup, watcher: Watcher
) -> None:
    _, _, webserver_mock, build_qpy_package_mock = watcher_mock_setup

    if server_crash:
        webserver_mock.__aenter__.side_effect = WorkerUnknownError(worker_name="mock")
    if build_error:
        build_qpy_package_mock.side_effect = PackageBuildError()

    webserver_runs = 1
    for build_runs in range(3):
        assert webserver_mock.__aenter__.call_count == webserver_runs
        assert build_qpy_package_mock.call_count == build_runs

        # Web server doesn't restart when the package build errors
        if not build_error:
            webserver_runs += 1

        # Simulate file change
        watcher._file_change.set()
        await asyncio.sleep(0)
