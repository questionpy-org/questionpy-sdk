#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Iterator
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPOk

from questionpy_sdk.webserver.routes.frontend import routes


@pytest.fixture
def mock_static_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    (tmp_path / "index.html").write_text("index content")
    (tmp_path / "asset.js").write_text("js content")
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "main.css").write_text("css content")

    with monkeypatch.context() as mp:
        mp.setattr("questionpy_sdk.webserver.routes.frontend.STATIC_DIR", tmp_path)
        yield tmp_path


@pytest.mark.app_routes(routes)
async def test_root_serves_index(client: TestClient, mock_static_dir: Path) -> None:
    resp = await client.get("/")
    assert resp.status == HTTPOk.status_code
    assert await resp.text() == "index content"


@pytest.mark.parametrize("path", ["/some/path/", "/some/route", "/another/path", "/deep/nested/route"])
@pytest.mark.app_routes(routes)
async def test_nested_path_serves_index(path: str, client: TestClient, mock_static_dir: Path) -> None:
    resp = await client.get(path)
    assert resp.status == HTTPOk.status_code
    assert await resp.text() == "index content"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/asset.js", "js content"),
        ("/styles/main.css", "css content"),
    ],
)
@pytest.mark.app_routes(routes)
async def test_existing_file_serves_file(path: str, expected: str, client: TestClient, mock_static_dir: Path) -> None:
    resp = await client.get(path)
    assert resp.status == HTTPOk.status_code
    assert await resp.text() == expected
