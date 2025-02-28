#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from http.client import UNPROCESSABLE_ENTITY
from typing import TYPE_CHECKING

from aiohttp import web

from questionpy import OptionsFormValidationError
from questionpy_sdk.webserver._form_data import flatten_form_data, parse_form_data
from questionpy_sdk.webserver.constants import API_PATH_PREFIX, DEFAULT_REQUEST_USER, WEBSERVER_KEY, StateFilename

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

MANIFEST_API_FIELDS = {
    "short_name",
    "namespace",
    "version",
    "api_version",
    "author",
    "name",
    "url",
    "languages",
    "description",
    "icon",
    "type",
    "license",
    "tags",
}

routes = web.RouteTableDef()


@routes.get("/manifest")
async def manifest(request: web.Request) -> web.Response:
    json_text = request.app[WEBSERVER_KEY].manifest.model_dump_json(include=MANIFEST_API_FIELDS)
    return web.json_response(text=json_text)


@routes.get("/options")
async def get_options(request: web.Request) -> web.Response:
    """Gets the options form definition that allows a question creator to customize a question."""
    webserver = request.app[WEBSERVER_KEY]
    question_state = webserver.read_state_file(StateFilename.QUESTION_STATE)

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        form_definition, _ = await worker.get_options_form(DEFAULT_REQUEST_USER, question_state)

    return web.json_response(text=form_definition.model_dump_json())


@routes.get("/options/state")
async def get_options_state(request: web.Request) -> web.Response:
    """Gets the form_data for the Options Form from the StateStorage."""
    webserver = request.app[WEBSERVER_KEY]
    question_state = webserver.read_state_file(StateFilename.QUESTION_STATE)

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        form_definition, form_data = await worker.get_options_form(DEFAULT_REQUEST_USER, question_state)

    section_names = [section.name for section in form_definition.sections]
    form_data = flatten_form_data(form_data, section_names)

    return web.json_response(form_data)


@routes.post("/options/state")
async def save_options_state(request: web.Request) -> web.Response:
    """Stores the form_data from the Options Form in the StateStorage."""
    webserver = request.app[WEBSERVER_KEY]
    form_data = parse_form_data(await request.json())
    old_state = webserver.read_state_file(StateFilename.QUESTION_STATE)

    try:
        worker: Worker
        async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
            question = await worker.create_question_from_options(DEFAULT_REQUEST_USER, old_state, form_data=form_data)
    except OptionsFormValidationError as err:
        return web.json_response(err.errors, status=UNPROCESSABLE_ENTITY)

    webserver.write_state_file(StateFilename.QUESTION_STATE, question.question_state)

    return web.json_response()


def serve_api(app: web.Application) -> None:
    api_app = web.Application()
    api_app[WEBSERVER_KEY] = app[WEBSERVER_KEY]
    api_app.add_routes(routes)
    app.add_subapp(API_PATH_PREFIX, api_app)
