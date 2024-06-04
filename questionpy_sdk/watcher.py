#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Self

from watchdog.events import (
    FileClosedEvent,
    FileOpenedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
    FileSystemMovedEvent,
)
from watchdog.observers import Observer
from watchdog.utils.event_debouncer import EventDebouncer

from questionpy_common.constants import DIST_DIR
from questionpy_sdk.package.builder import DirPackageBuilder
from questionpy_sdk.package.errors import PackageBuildError, PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource
from questionpy_sdk.webserver.app import WebServer
from questionpy_server.worker.runtime.package_location import DirPackageLocation

if TYPE_CHECKING:
    from watchdog.observers.api import ObservedWatch

log = logging.getLogger("questionpy-sdk:watcher")

_DEBOUNCE_INTERVAL = 0.5  # seconds


class _EventHandler(FileSystemEventHandler):
    """Debounces events for watchdog file monitoring, ignoring events in the `dist` directory."""

    def __init__(
        self, loop: asyncio.AbstractEventLoop, notify_callback: Callable[[], Awaitable[None]], watch_path: Path
    ) -> None:
        self._loop = loop
        self._notify_callback = notify_callback
        self._watch_path = watch_path

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
        asyncio.run_coroutine_threadsafe(self._notify_callback(), self._loop)

    def _ignore_event(self, event: FileSystemEvent) -> bool:
        """Ignores events that should not trigger a rebuild.

        Args:
            event: The event to check.

        Returns:
            `True` if event should be ignored, otherwise `False`.
        """
        if isinstance(event, FileOpenedEvent | FileClosedEvent):
            return True

        # ignore events events in `dist` dir
        relevant_path = event.dest_path if isinstance(event, FileSystemMovedEvent) else event.src_path
        try:
            return Path(relevant_path).relative_to(self._watch_path).parts[0] == DIST_DIR
        except IndexError:
            return False


class Watcher(AbstractAsyncContextManager):
    """Watch a package source path and rebuild package/restart server on file changes."""

    def __init__(
        self, source_path: Path, pkg_location: DirPackageLocation, state_storage_path: Path, host: str, port: int
    ) -> None:
        self._source_path = source_path
        self._pkg_location = pkg_location
        self._host = host
        self._port = port

        self._event_handler = _EventHandler(asyncio.get_running_loop(), self._notify, self._source_path)
        self._observer = Observer()
        self._webserver = WebServer(self._pkg_location, state_storage_path, self._host, self._port)
        self._on_change_event = asyncio.Event()
        self._watch: ObservedWatch | None = None

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
        await self._webserver.stop_server()

    def _schedule(self) -> None:
        if self._watch is None:
            log.debug("Starting file watching...")
            self._watch = self._observer.schedule(self._event_handler, self._source_path, recursive=True)

    def _unschedule(self) -> None:
        if self._watch:
            log.debug("Stopping file watching...")
            self._observer.unschedule(self._watch)
            self._watch = None

    async def _notify(self) -> None:
        self._on_change_event.set()

    async def run_forever(self) -> None:
        try:
            await self._webserver.start_server()
        except Exception:
            log.exception("Failed to start webserver. The exception was:")
            # When user messed up the their package on initial run, we just bail out.
            return

        self._schedule()

        while True:
            await self._on_change_event.wait()

            # Try to rebuild package and restart web server which might fail.
            self._unschedule()
            await self._rebuild_and_restart()
            self._schedule()

            self._on_change_event.clear()

    async def _rebuild_and_restart(self) -> None:
        log.info("File changes detected. Rebuilding package...")

        # Stop webserver.
        try:
            await self._webserver.stop_server()
        except Exception:
            log.exception("Failed to stop web server. The exception was:")
            raise  # Should not happen, thus we're propagating.

        # Build package.
        try:
            package_source = PackageSource(self._source_path)
            with DirPackageBuilder(package_source) as builder:
                builder.write_package()
        except (PackageBuildError, PackageSourceValidationError):
            log.exception("Failed to build package. The exception was:")
            return

        # Start server.
        try:
            await self._webserver.start_server()
        except Exception:
            log.exception("Failed to start web server. The exception was:")
