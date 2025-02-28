#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from http.client import UNPROCESSABLE_ENTITY
from typing import TYPE_CHECKING, Never
from uuid import uuid4

import aiohttp_jinja2
from aiohttp import web

from questionpy import OptionsFormValidationError
from questionpy_sdk.webserver_legacy._form_data import get_nested_form_data, parse_form_data
from questionpy_sdk.webserver_legacy.app import DEFAULT_REQUEST_USER, SDK_WEBSERVER_APP_KEY, StateFilename, WebServer
from questionpy_sdk.webserver_legacy.context import contextualize

if TYPE_CHECKING:
    from questionpy_server.worker import Worker

routes = web.RouteTableDef()


@routes.get("/")
async def render_options(request: web.Request) -> web.Response:
    """Gets the options form definition that allows a question creator to customize a question."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    question_state = webserver.read_state_file(StateFilename.QUESTION_STATE)

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, form_data = await worker.get_options_form(DEFAULT_REQUEST_USER, question_state)

    context = {
        "manifest": manifest,
        "options": contextualize(form_definition=form_definition, form_data=form_data).model_dump(),
    }

    return aiohttp_jinja2.render_template("options.html.jinja2", request, context)


async def _save_updated_form_data(form_data: dict, webserver: "WebServer") -> None:
    old_state = webserver.read_state_file(StateFilename.QUESTION_STATE)
    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        question = await worker.create_question_from_options(DEFAULT_REQUEST_USER, old_state, form_data=form_data)

    webserver.write_state_file(StateFilename.QUESTION_STATE, question.question_state)


@routes.post("/submit")
async def submit_form(request: web.Request) -> web.Response:
    """Stores the form_data from the Options Form in the StateStorage."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    form_data = parse_form_data(await request.json())

    try:
        await _save_updated_form_data(form_data, webserver)
    except OptionsFormValidationError as err:
        return web.json_response(err.errors, status=UNPROCESSABLE_ENTITY)

    return web.Response()


@routes.post("/repeat")
async def repeat_element(request: web.Request) -> web.Response:
    """Adds Repetitions to the referenced RepetitionElement and store the form_data in the StateStorage."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    data = await request.json()
    question_form_data = parse_form_data(data["form_data"])
    repetition_list = get_nested_form_data(question_form_data, data["repetition_name"])

    if not isinstance(repetition_list, list) or "increment" not in data:
        raise web.HTTPUnprocessableEntity

    new_repetition_items: list[dict] = [repetition_list[-1].copy() for _ in range(int(data["increment"]))]
    # ID elements must be unique, so new items need a new value.
    for new_repetition_item in new_repetition_items:
        id_element_names = new_repetition_item.get("qpy_id_elements")
        if not isinstance(id_element_names, list):
            continue

        for id_element_name in id_element_names:
            if id_element_name in new_repetition_item:
                new_repetition_item[id_element_name] = str(uuid4())

    repetition_list.extend(new_repetition_items)

    try:
        await _save_updated_form_data(question_form_data, webserver)
    except OptionsFormValidationError as err:
        return web.json_response(err.errors, status=UNPROCESSABLE_ENTITY)

    raise web.HTTPFound("/")  # noqa: EM101


@routes.post("/options/remove-repetition")
async def remove_element(request: web.Request) -> web.Response:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    data = await request.json()
    question_form_data = parse_form_data(data["form_data"])
    repetition_list = get_nested_form_data(question_form_data, data["repetition_name"])
    if isinstance(repetition_list, list) and "index" in data:
        del repetition_list[int(data["index"])]

    try:
        await _save_updated_form_data(question_form_data, webserver)
    except OptionsFormValidationError as err:
        return web.json_response(err.errors, status=UNPROCESSABLE_ENTITY)

    raise web.HTTPFound("/")  # noqa: EM101


@routes.post("/delete-question-state")
async def delete_question_state(request: web.Request) -> Never:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    # When deleting a question, it seems sensible to also delete any attempts at that question, so we delete all state
    # files.
    webserver.delete_state_files(*StateFilename)
    raise web.HTTPFound("/")  # noqa: EM101
