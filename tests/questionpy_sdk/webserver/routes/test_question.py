#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import ANY, AsyncMock, Mock

import pytest
from aiohttp import FormData
from aiohttp.test_utils import TestClient
from aiohttp.web_exceptions import HTTPConflict, HTTPNotFound, HTTPOk, HTTPUnprocessableEntity

from questionpy import OptionsFormValidationError
from questionpy.form import OptionsFile
from questionpy_common.elements import OptionsFormDefinition
from questionpy_sdk.webserver.errors import DuplicateQuestionError, MissingQuestionStateError
from questionpy_sdk.webserver.routes.question import routes


@pytest.fixture
def options_file() -> OptionsFile:
    return OptionsFile(
        path="/",
        filename="test_file.txt",
        file_ref="dbabd43828eccd27e3a109b58454e4ff43c8673e",
        size=17,
        uploaded_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
        mime_type="text/plain",
    )


@pytest.mark.app_routes(routes)
async def test_get_question(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_form_definition.return_value = OptionsFormDefinition()

    async with client.get("/question/myuQ2JWl") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["general"] == []


@pytest.mark.app_routes(routes)
async def test_delete_question(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.delete("/question/myuQ2JWl") as resp:
        assert resp.status == HTTPOk.status_code
    mock_controller.delete_question.assert_awaited_once_with("myuQ2JWl")


@pytest.mark.app_routes(routes)
async def test_get_questions(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_questions.return_value = {"myuQ2JWl": {}, "xTXbLYfl": {}}

    async with client.get("/questions") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data == {"myuQ2JWl": {}, "xTXbLYfl": {}}


@pytest.mark.app_routes(routes)
async def test_delete_questions(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.delete("/questions") as resp:
        assert resp.status == HTTPOk.status_code
    mock_controller.delete_all_questions.assert_awaited_once()


@pytest.mark.app_routes(routes)
async def test_get_question_state(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.get_options_state.return_value = {"foo": "bar"}

    async with client.get("/question/myuQ2JWl/state") as resp:
        assert resp.status == HTTPOk.status_code
        data = await resp.json()
        assert data["foo"] == "bar"


@pytest.mark.app_routes(routes)
async def test_post_question_state(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/question/myuQ2JWl/state", json={"foo": "bar"}) as resp:
        assert resp.status == HTTPOk.status_code
    mock_controller.save_options_state.assert_awaited_once()


@pytest.mark.app_routes(routes)
async def test_post_question_state_validation_error(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.save_options_state.side_effect = OptionsFormValidationError({"some": "error"})

    async with client.post("/question/myuQ2JWl/state", json={"foo": "bar"}) as resp:
        assert resp.status == HTTPUnprocessableEntity.status_code
        data = await resp.json()
        assert data["some"] == "error"


@pytest.mark.app_routes(routes)
async def test_post_question_clone(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/question/myuQ2JWl/clone/Bu2boh5u") as resp:
        assert resp.status == HTTPOk.status_code
        mock_controller.clone_question.assert_awaited_once_with("myuQ2JWl", "Bu2boh5u")


@pytest.mark.app_routes(routes)
async def test_post_question_clone_not_found(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.clone_question.side_effect = MissingQuestionStateError

    async with client.post("/question/myuQ2JWl/clone/Bu2boh5u") as resp:
        assert resp.status == HTTPNotFound.status_code


@pytest.mark.app_routes(routes)
async def test_post_question_clone_duplicate(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.clone_question.side_effect = DuplicateQuestionError

    async with client.post("/question/myuQ2JWl/clone/Bu2boh5u") as resp:
        assert resp.status == HTTPConflict.status_code


@pytest.mark.app_routes(routes)
async def test_get_question_file(client: TestClient, mock_controller: AsyncMock, options_file: OptionsFile) -> None:
    mock_file_reader = Mock()
    mock_file_reader.__enter__ = Mock(return_value=mock_file_reader)
    mock_file_reader.__exit__ = Mock(return_value=None)
    mock_file_reader.read = Mock(side_effect=[b"some test content"])
    mock_controller.get_file.return_value = (options_file, mock_file_reader)

    async with client.get("/question/myuQ2JWl/file/my_file_upload/dbabd43828eccd27e3a109b58454e4ff43c8673e") as resp:
        mock_controller.get_file.assert_awaited_once_with(
            "myuQ2JWl", "my_file_upload", "dbabd43828eccd27e3a109b58454e4ff43c8673e"
        )

        assert resp.status == HTTPOk.status_code
        assert resp.headers["Content-Type"] == "text/plain"
        assert resp.headers["Last-Modified"] == "Wed, 01 Jan 2025 12:00:00 GMT"
        assert resp.headers["Content-Length"] == "17"
        assert "immutable" in resp.headers["Cache-Control"]
        assert "test_file.txt" in resp.headers["Content-Disposition"]
        assert await resp.text() == "some test content"


@pytest.mark.app_routes(routes)
async def test_post_question_file_upload_single_file(
    client: TestClient, mock_controller: AsyncMock, options_file: OptionsFile
) -> None:
    mock_controller.add_file.return_value = options_file

    data = FormData()
    data.add_field("file", b"some test content", filename="test.txt", content_type="text/plain")

    async with client.post("/question/file-upload", data=data) as resp:
        assert resp.status == HTTPOk.status_code
        response_data = await resp.json()
        assert len(response_data) == 1
        of = response_data[0]
        assert of["filename"] == "test_file.txt"
        assert of["file_ref"] == "dbabd43828eccd27e3a109b58454e4ff43c8673e"
        assert of["size"] == 17
        assert of["mime_type"] == "text/plain"
        assert of["uploaded_at"] == "2025-01-01T12:00:00Z"
        assert of["path"] == "/"
        mock_controller.add_file.assert_awaited_once_with("test.txt", "text/plain", ANY)


@pytest.mark.app_routes(routes)
async def test_post_question_file_upload_multiple_files(client: TestClient, mock_controller: AsyncMock) -> None:
    mock_controller.add_file.side_effect = [
        OptionsFile(
            path="/",
            filename="test1.jpg",
            file_ref="041bb7ae61ffe07323f642b8c72ba96c72c5d2b0",
            size=11,
            uploaded_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            mime_type="image/jpeg",
        ),
        OptionsFile(
            path="/",
            filename="test2.jpg",
            file_ref="c84ce717f09efd2583ca97d3feb69a333e342b5a",
            size=11,
            uploaded_at=datetime(2025, 1, 1, 12, 0, 1, tzinfo=UTC),
            mime_type="image/jpeg",
        ),
    ]

    data = FormData()
    data.add_field("file", b"jpgcontent1", filename="test1.jpg", content_type="image/jpeg")
    data.add_field("file", b"jpgcontent2", filename="test2.jpg", content_type="image/jpeg")

    async with client.post("/question/file-upload", data=data) as resp:
        assert resp.status == HTTPOk.status_code
        response_data = await resp.json()
        assert len(response_data) == 2
        of1, of2 = response_data

        assert of1["filename"] == "test1.jpg"
        assert of1["file_ref"] == "041bb7ae61ffe07323f642b8c72ba96c72c5d2b0"
        assert of1["size"] == 11
        assert of1["mime_type"] == "image/jpeg"
        assert of1["uploaded_at"] == "2025-01-01T12:00:00Z"
        assert of1["path"] == "/"

        assert of2["filename"] == "test2.jpg"
        assert of2["file_ref"] == "c84ce717f09efd2583ca97d3feb69a333e342b5a"
        assert of2["size"] == 11
        assert of2["mime_type"] == "image/jpeg"
        assert of2["uploaded_at"] == "2025-01-01T12:00:01Z"
        assert of2["path"] == "/"

        assert mock_controller.add_file.call_count == 2


@pytest.mark.app_routes(routes)
async def test_post_question_file_upload_no_file(client: TestClient, mock_controller: AsyncMock) -> None:
    async with client.post("/question/file-upload", data=FormData(default_to_multipart=True)) as resp:
        assert resp.status == HTTPUnprocessableEntity.status_code
        data = await resp.json()
        assert data["error"] == "No files in form data"
        mock_controller.add_file.assert_not_called()


@pytest.mark.app_routes(routes)
async def test_post_question_file_upload_wrong_part_name(client: TestClient, mock_controller: AsyncMock) -> None:
    data = FormData()
    data.add_field("wrongname", b"content", filename="test.txt", content_type="text/plain")

    async with client.post("/question/file-upload", data=data) as resp:
        assert resp.status == HTTPUnprocessableEntity.status_code
        response_data = await resp.json()
        assert response_data["error"] == "Expected part name to be 'file'"
        mock_controller.add_file.assert_not_called()


@pytest.mark.app_routes(routes)
async def test_post_question_file_upload_missing_filename(client: TestClient, mock_controller: AsyncMock) -> None:
    data = FormData()
    data.add_field("file", BytesIO(b"content"), filename="", content_type="text/plain")

    async with client.post("/question/file-upload", data=data) as resp:
        assert resp.status == HTTPUnprocessableEntity.status_code
        response_data = await resp.json()
        assert response_data["error"] == "Missing filename"
        mock_controller.add_file.assert_not_called()
