#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING

from aiohttp import BodyPartReader, web
from aiohttp.web_exceptions import HTTPNotFound, HTTPUnprocessableEntity
from pydantic import RootModel

from questionpy import OptionsFormValidationError
from questionpy_sdk.webserver.constants import FILE_REF_RE, ID_RE
from questionpy_sdk.webserver.controllers.question import QuestionController
from questionpy_sdk.webserver.errors import DuplicateQuestionError, MissingQuestionStateError
from questionpy_sdk.webserver.routes.base import BaseView

if TYPE_CHECKING:
    from questionpy.form import OptionsFile

routes = web.RouteTableDef()


class QuestionBaseView(BaseView["QuestionController"]):
    controller_class = QuestionController


@routes.view(f"/question/{{question_id:{ID_RE}}}", name="question")
class QuestionView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets the options form definition that allows a question creator to customize a question."""
        question_id = self.request.match_info["question_id"]
        return self.json_model_response(await self.controller.get_form_definition(question_id))

    async def delete(self) -> web.Response:
        """Deletes the question and its attempts from the state storage."""
        question_id = self.request.match_info["question_id"]

        try:
            await self.controller.delete_question(question_id)
        except MissingQuestionStateError as err:
            raise HTTPNotFound from err

        return self.json_success_response()


@routes.view("/questions", name="question.list")
class QuestionListView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets a list of all saved questions for the current package."""
        data = await self.controller.get_questions()
        return self.json_model_response(RootModel(data))

    async def delete(self) -> web.Response:
        """Deletes all questions and its attempts from the state storage."""
        await self.controller.delete_all_questions()
        return self.json_success_response()


@routes.view(f"/question/{{question_id:{ID_RE}}}/state", name="question.state")
class QuestionStateView(QuestionBaseView):
    async def get(self) -> web.Response:
        """Gets the form data for the Options Form from the state storage."""
        question_id = self.request.match_info["question_id"]
        state_response = await self.controller.get_options_state(question_id)
        return self.json_model_response(RootModel(state_response))

    async def post(self) -> web.Response:
        """Stores the form data from the Options Form in the state storage."""
        question_id = self.request.match_info["question_id"]
        form_data = await self.request.json()

        try:
            await self.controller.save_options_state(question_id, form_data)
        except OptionsFormValidationError as err:
            return web.json_response(err.errors, status=HTTPUnprocessableEntity.status_code)

        return self.json_success_response()


@routes.view(f"/question/{{question_id:{ID_RE}}}/clone/{{new_question_id:{ID_RE}}}", name="question.clone")
class QuestionCloneView(QuestionBaseView):
    async def post(self) -> web.Response:
        """Clones a question."""
        question_id = self.request.match_info["question_id"]
        new_question_id = self.request.match_info["new_question_id"]

        try:
            await self.controller.clone_question(question_id, new_question_id)
        except MissingQuestionStateError as err:
            raise HTTPNotFound from err
        except DuplicateQuestionError as err:
            raise web.HTTPConflict(text=str(err)) from err

        return self.json_success_response()


@routes.view(f"/question/{{question_id:{ID_RE}}}/file/{{name}}/{{file_ref:{FILE_REF_RE}}}", name="question.file")
class QuestionFileView(QuestionBaseView):
    async def get(self) -> web.StreamResponse:
        """Retrieves an option file."""
        question_id = self.request.match_info["question_id"]
        name = self.request.match_info["name"]
        file_ref = self.request.match_info["file_ref"]

        options_file, file_reader = await self.controller.get_file(question_id, name, file_ref)

        headers = {
            # Content-addressable -> never changes
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": f'inline; filename="{options_file.filename}"',
            "Content-Length": str(options_file.size),
            "Content-Type": options_file.mime_type,
            "Last-Modified": options_file.uploaded_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        }

        resp = web.StreamResponse(headers=headers)
        await resp.prepare(self.request)

        # stream in chunks
        chunk_size = 64 * 1024  # 64 KiB
        with file_reader as f:
            while chunk := f.read(chunk_size):
                await resp.write(chunk)
        await resp.write_eof()

        return resp


@routes.view("/question/file-upload", name="question.file-upload")
class QuestionFileUploadView(QuestionBaseView):
    async def post(self) -> web.Response:
        """Processes and stores option files."""
        files: list[OptionsFile] = []

        async for part in await self.request.multipart():
            if isinstance(part, BodyPartReader):
                if part.name != "file":
                    return web.json_response(
                        {"error": "Expected part name to be 'file'"}, status=HTTPUnprocessableEntity.status_code
                    )

                if not part.filename:
                    return web.json_response({"error": "Missing filename"}, status=HTTPUnprocessableEntity.status_code)

                file = await self.controller.add_file(
                    part.filename,
                    part.headers.get("Content-Type", "application/octet-stream"),
                    part,
                )
                files.append(file)

        if len(files) == 0:
            return web.json_response({"error": "No files in form data"}, status=HTTPUnprocessableEntity.status_code)

        return self.json_model_response(RootModel(files))
