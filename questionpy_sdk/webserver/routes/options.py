#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Never

import aiohttp_jinja2
from aiohttp import web

from questionpy_common.environment import RequestUser
from questionpy_sdk.webserver._form_data import get_nested_form_data, parse_form_data
from questionpy_sdk.webserver.app import SDK_WEBSERVER_APP_KEY, WebServer
from questionpy_sdk.webserver.context import contextualize

routes = web.RouteTableDef()


@routes.get("/")
async def render_options(request: web.Request) -> web.Response:
    """Gets the options form definition that allows a question creator to customize a question."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    question_state = webserver.load_question_state()

    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), question_state)

    context = {
        "manifest": manifest,
        "options": contextualize(form_definition=form_definition, form_data=form_data).model_dump(),
    }

    return aiohttp_jinja2.render_template("options.html.jinja2", request, context)


async def _save_updated_form_data(form_data: dict, webserver: "WebServer") -> None:
    old_state = webserver.load_question_state()
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        question = await worker.create_question_from_options(RequestUser(["de", "en"]), old_state, form_data=form_data)

    webserver.save_question_state(question.question_state)


@routes.post("/submit")
async def submit_form(request: web.Request) -> web.Response:
    """Stores the form_data from the Options Form in the StateStorage."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    form_data = parse_form_data(await request.json())
    await _save_updated_form_data(form_data, webserver)

    return web.Response(status=201)


@routes.post("/repeat")
async def repeat_element(request: web.Request) -> Never:
    """Adds Repetitions to the referenced RepetitionElement and store the form_data in the StateStorage."""
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    data = await request.json()
    question_form_data = parse_form_data(data["form_data"])
    repetition_list = get_nested_form_data(question_form_data, data["repetition_name"])
    if isinstance(repetition_list, list) and "increment" in data:
        repetition_list.extend([repetition_list[-1]] * int(data["increment"]))

    await _save_updated_form_data(question_form_data, webserver)
    raise web.HTTPFound("/")  # noqa: EM101


@routes.post("/options/remove-repetition")
async def remove_element(request: web.Request) -> Never:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    data = await request.json()
    question_form_data = parse_form_data(data["form_data"])
    repetition_list = get_nested_form_data(question_form_data, data["repetition_name"])
    if isinstance(repetition_list, list) and "index" in data:
        del repetition_list[int(data["index"])]

    await _save_updated_form_data(question_form_data, webserver)
    raise web.HTTPFound("/")  # noqa: EM101


@routes.post("/delete-question-state")
async def delete_question_state(request: web.Request) -> Never:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    webserver.delete_question_state()
    raise web.HTTPFound("/")  # noqa: EM101
