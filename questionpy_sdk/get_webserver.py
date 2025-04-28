#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from typing import Protocol

from questionpy_server.worker.runtime.package_location import PackageLocation


class WebServerProtocol(Protocol):
    async def run_forever(self) -> None: ...
    async def stop_server(self) -> None: ...
    async def start_server(self) -> None: ...


def get_webserver(
    package_location: PackageLocation,
    state_storage_path: Path,
    host: str,
    port: int,
    *,
    legacy_frontend: bool = False,
) -> WebServerProtocol:
    if legacy_frontend:
        from questionpy_sdk.webserver_legacy.app import WebServer as WebServerLegacy  # noqa: PLC0415

        return WebServerLegacy(package_location, state_storage_path, host, port)

    from questionpy_sdk.webserver import WebServer as WebServerSpa  # noqa: PLC0415

    return WebServerSpa(package_location, state_storage_path, host, port)
