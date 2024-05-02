#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from typing import TYPE_CHECKING

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest

from questionpy_common.environment import RequestUser
from questionpy_sdk.webserver.context import contextualize
from questionpy_sdk.webserver.state_storage import add_repetition, parse_form_data
from questionpy_server.worker.runtime.messages import WorkerUnknownError

if TYPE_CHECKING:
    from questionpy_common.elements import OptionsFormDefinition
    from questionpy_sdk.webserver.app import WebServer
    from questionpy_server.worker.worker import Worker

routes = web.RouteTableDef()


@routes.get("/")
async def render_options(request: web.Request) -> web.Response:
    """Gets the options form definition that allows a question creator to customize a question."""
    webserver: "WebServer" = request.app["sdk_webserver_app"]
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), old_state)

    context = {
        "manifest": manifest,
        "options": contextualize(form_definition=form_definition, form_data=form_data).model_dump(),
    }

    return aiohttp_jinja2.render_template("options.html.jinja2", request, context)


@routes.post("/submit")
async def submit_form(request: web.Request) -> web.Response:
    """Stores the form_data from the Options Form in the StateStorage."""
    webserver: "WebServer" = request.app["sdk_webserver_app"]
    data = await request.json()
    parsed_form_data = parse_form_data(data)
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        try:
            question = await worker.create_question_from_options(
                RequestUser(["de", "en"]), old_state, form_data=parsed_form_data
            )
        except WorkerUnknownError as exc:
            raise HTTPBadRequest from exc

    new_state = question.question_state
    webserver.state_storage.insert(webserver.package_location, json.loads(new_state))

    return web.Response(status=201)


@routes.post("/repeat")
async def repeat_element(request: web.Request) -> web.Response:
    """Adds Repetitions to the referenced RepetitionElement and store the form_data in the StateStorage."""
    webserver: "WebServer" = request.app["sdk_webserver_app"]
    data = await request.json()
    old_form_data = add_repetition(
        form_data=parse_form_data(data["form_data"]),
        reference=data["element-name"].replace("]", "").split("["),
        increment=int(data["increment"]),
    )
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        try:
            question = await worker.create_question_from_options(
                RequestUser(["de", "en"]), old_state, form_data=old_form_data
            )
        except WorkerUnknownError as exc:
            raise HTTPBadRequest from exc

        new_state = question.question_state
        webserver.state_storage.insert(webserver.package_location, json.loads(new_state))
        form_definition: OptionsFormDefinition
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), new_state)

    context = {
        "manifest": manifest,
        "options": contextualize(form_definition=form_definition, form_data=form_data).model_dump(),
    }

    return aiohttp_jinja2.render_template("options.html.jinja2", request, context)
