#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
from pathlib import Path
from typing import cast

import pytest
from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileClosedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileOpenedEvent,
    FileSystemEvent,
)

from questionpy_common.constants import DIST_DIR
from questionpy_sdk.watcher import _EventHandler

some_path = Path("/", "path", "to")


@pytest.fixture
def event_handler() -> _EventHandler:
    async def notify() -> None:
        pass

    mock_loop = cast(asyncio.AbstractEventLoop, None)
    return _EventHandler(mock_loop, notify, some_path)


@pytest.mark.parametrize(
    "event",
    [
        DirCreatedEvent(src_path=str(some_path / "foo")),
        DirDeletedEvent(src_path=str(some_path / "foo")),
        DirModifiedEvent(src_path=str(some_path / "foo")),
        DirMovedEvent(src_path=str(some_path / DIST_DIR / "foo"), dest_path=str(some_path / "foo")),
        FileCreatedEvent(src_path=str(some_path / "foo")),
        FileCreatedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        FileDeletedEvent(src_path=str(some_path / "foo")),
        FileDeletedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        FileModifiedEvent(src_path=str(some_path)),
        FileModifiedEvent(src_path=str(some_path / "python" / "foo" / "bar" / "module.py")),
        FileMovedEvent(src_path=str(some_path / DIST_DIR / "foo"), dest_path=str(some_path / "foo")),
    ],
)
def test_should_not_ignore_events(event: FileSystemEvent, event_handler: _EventHandler) -> None:
    assert not event_handler._ignore_event(event)


# test that the watcher is ignoring certain events, like moving a file into the `dist` folder
@pytest.mark.parametrize(
    "event",
    [
        DirCreatedEvent(src_path=str(some_path / DIST_DIR / "foo")),
        DirDeletedEvent(src_path=str(some_path / DIST_DIR / "foo")),
        DirModifiedEvent(src_path=str(some_path / DIST_DIR / "foo")),
        FileClosedEvent(src_path=str(some_path / "foo")),
        DirMovedEvent(src_path=str(some_path / "foo"), dest_path=str(some_path / DIST_DIR / "foo")),
        FileCreatedEvent(src_path=str(some_path / DIST_DIR / "foo")),
        FileDeletedEvent(src_path=str(some_path / DIST_DIR / "foo")),
        FileModifiedEvent(src_path=str(some_path / DIST_DIR)),
        FileMovedEvent(src_path=str(some_path / "foo"), dest_path=str(some_path / DIST_DIR / "foo")),
        FileOpenedEvent(src_path=str(some_path / "foo")),
    ],
)
def test_should_ignore_events(event: FileSystemEvent, event_handler: _EventHandler) -> None:
    assert event_handler._ignore_event(event)
