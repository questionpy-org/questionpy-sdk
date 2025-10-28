#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from questionpy_common.manifest import Bcp47LanguageTag, Manifest


@pytest.fixture
def mock_worker() -> AsyncMock:
    manifest = Manifest(
        short_name="my_short_name",
        version="7.3.1",
        api_version="9.4",
        author="Testy McTestface",
        name={Bcp47LanguageTag("en"): "Test Package"},
        languages=[Bcp47LanguageTag("en")],
    )
    return AsyncMock(get_manifest=AsyncMock(return_value=manifest))


@pytest.fixture
def mock_worker_pool(monkeypatch: pytest.MonkeyPatch, mock_worker: AsyncMock) -> Iterator[tuple[Mock, MagicMock]]:
    with monkeypatch.context() as mp:
        mock_get_worker_cm = MagicMock(__aenter__=AsyncMock(return_value=mock_worker))
        mock_worker_pool = MagicMock(get_worker=Mock(return_value=mock_get_worker_cm))
        mock_worker_pool_cls = Mock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_worker_pool)))
        mp.setattr("questionpy_sdk.webserver.server.WorkerPool", mock_worker_pool_cls)
        yield mock_worker_pool_cls, mock_worker_pool


@pytest.fixture
def mock_web_components(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Mock, AsyncMock]]:
    with monkeypatch.context() as mp:
        mock_app_runner = AsyncMock()
        mp.setattr("questionpy_sdk.webserver.server.web.AppRunner", Mock(return_value=mock_app_runner))
        mock_tcp_site = Mock(return_value=Mock(start=AsyncMock()))
        mp.setattr("questionpy_sdk.webserver.server.web.TCPSite", mock_tcp_site)
        yield mock_app_runner, mock_tcp_site
