#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Self, Unpack

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
    FileSystemMovedEvent,
)
from watchdog.observers import Observer
from watchdog.utils.event_debouncer import EventDebouncer

from questionpy_sdk._package import build_qpy_package
from questionpy_sdk._package._ignores import create_ignore_file_callable
from questionpy_sdk._package.errors import PackageError
from questionpy_sdk._package.source import PackageSource
from questionpy_sdk.webserver import WebServer
from questionpy_sdk.webserver.server import WebServerArgs
from questionpy_server.worker.runtime.messages import BaseWorkerError

if TYPE_CHECKING:
    from watchdog.observers.api import ObservedWatch

log = logging.getLogger("questionpy-sdk:watcher")

_DEBOUNCE_INTERVAL = 1  # seconds


class _EventHandler(FileSystemEventHandler):
    """Handles filesystem events with debouncing and ignores paths based on a provided filter."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        notify_callback: Callable[[], None],
        watch_path: Path,
        ignore_path: Callable[[Path], bool],
    ) -> None:
        self._loop = loop
        self._notify_callback = notify_callback
        self._watch_path = watch_path
        self._ignore_path = ignore_path

        self._event_debouncer = EventDebouncer(_DEBOUNCE_INTERVAL, self._on_file_changes)

    def start(self) -> None:
        self._event_debouncer.start()

    def stop(self) -> None:
        if self._event_debouncer.is_alive():
            self._event_debouncer.stop()
            self._event_debouncer.join()

    def dispatch(self, event: FileSystemEvent) -> None:
        # filter events and debounce
        if not self._ignore_event(event):
            self._event_debouncer.handle_event(event)

    def _on_file_changes(self, events: list[FileSystemEvent]) -> None:
        # skip synchronization hassle by delegating this to the event loop in the main thread
        self._loop.call_soon_threadsafe(self._notify_callback)

    def _ignore_event(self, event: FileSystemEvent) -> bool:
        """Ignores events that should not trigger a rebuild.

        Args:
            event: The event to check.

        Returns:
            `True` if event should be ignored, otherwise `False`.
        """
        # only consider file modification events
        if not isinstance(event, FileDeletedEvent | FileModifiedEvent | FileCreatedEvent | FileMovedEvent):
            return True

        # for move events we need to consider both, `src_path` and `dest_path`
        check_paths = {event.src_path, event.dest_path} if isinstance(event, FileSystemMovedEvent) else {event.src_path}

        return all(self._ignore_path(self._get_rel_path(path)) for path in check_paths)

    def _get_rel_path(self, path: bytes | str) -> Path:
        path_str = path.decode() if isinstance(path, bytes) else path
        return Path(path_str).relative_to(self._watch_path)


class Watcher(AbstractAsyncContextManager):
    """Watch a package source path and rebuild package/restart server on file changes."""

    def __init__(self, source_path: Path, **webserver_args: Unpack[WebServerArgs]) -> None:
        self._source_path = source_path
        self._webserver_args = webserver_args

        self._file_change = asyncio.Event()
        self._observer = Observer()
        self._watch: ObservedWatch | None = None

        additional_ignores = [*PackageSource(source_path).config.ignore, ".gitignore"]
        ignore_file = create_ignore_file_callable(source_path, additional_ignores)
        loop = asyncio.get_running_loop()
        self._event_handler = _EventHandler(loop, self._file_change.set, self._source_path, ignore_file)

    async def __aenter__(self) -> Self:
        self._event_handler.start()
        self._observer.start()
        log.info("Watching '%s' for changes...", self._source_path)

        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if self._observer.is_alive():
            self._observer.stop()
        self._event_handler.stop()

    def _schedule(self) -> None:
        if self._watch is None:
            log.debug("Starting file watching...")
            self._file_change.clear()
            self._watch = self._observer.schedule(self._event_handler, str(self._source_path), recursive=True)

    def _unschedule(self) -> None:
        if self._watch:
            log.debug("Stopping file watching...")
            self._observer.unschedule(self._watch)
            self._watch = None

    async def run_forever(self) -> None:
        async def wait_for_changes() -> None:
            log.info("Waiting for file change before attempting to rebuild...")
            self._schedule()
            await self._file_change.wait()

        while True:
            # Run web server
            self._schedule()
            try:
                async with WebServer(**self._webserver_args):
                    await self._file_change.wait()
            except BaseWorkerError:
                log.exception("Failed to start web server.")
                await wait_for_changes()

            # Rebuild package
            while True:
                self._unschedule()
                log.info("File change detected. Rebuilding package...")
                try:
                    package_source = PackageSource(self._source_path)
                    build_qpy_package(package_source)
                except PackageError:
                    log.exception("Failed to build package.")
                    await wait_for_changes()
                else:
                    break
