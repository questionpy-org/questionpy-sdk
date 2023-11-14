#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from pathlib import Path
from typing import Optional

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
from jinja2 import FileSystemLoader
from questionpy_common.constants import MiB
from questionpy_common.elements import OptionsFormDefinition
from questionpy_common.environment import RequestUser
from questionpy_server import WorkerPool
from questionpy_server.worker.worker import Worker
from questionpy_server.worker.exception import WorkerUnknownError
from questionpy_server.worker.worker.thread import ThreadWorker

from questionpy_sdk.webserver.state_storage import QuestionStateStorage, add_repetition, parse_form_data

routes = web.RouteTableDef()


class WebServer:

    def __init__(self, package: Path):
        self.web_app = web.Application()
        webserver_path = Path(__file__).parent
        routes.static('/static', webserver_path / 'static')
        self.web_app.add_routes(routes)
        self.web_app['sdk_webserver_app'] = self

        self.template_folder = webserver_path / 'templates'
        jinja2_extensions = ['jinja2.ext.do']
        aiohttp_jinja2.setup(self.web_app,
                             loader=FileSystemLoader(self.template_folder),
                             extensions=jinja2_extensions)
        self.worker_pool = WorkerPool(1, 500 * MiB, worker_type=ThreadWorker)
        self.package = package
        self.state_storage = QuestionStateStorage()

    def start_server(self) -> None:
        web.run_app(self.web_app)


@routes.get('/')
async def render_options(request: web.Request) -> web.Response:
    """Get the options form definition that allows a question creator to customize a question."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package)
    old_state: Optional[bytes] = json.dumps(stored_state).encode() if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), old_state)

    context = {
        'manifest': manifest,
        'options': form_definition.model_dump(),
        'form_data': form_data
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


@routes.post('/submit')
async def submit_form(request: web.Request) -> web.Response:
    """Store the form_data from the Options Form in the StateStorage."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    data = await request.json()
    parsed_form_data = parse_form_data(data)
    stored_state = webserver.state_storage.get(webserver.package)
    old_state: Optional[bytes] = json.dumps(stored_state).encode() if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        try:
            question = await worker.create_question_from_options(RequestUser(["de", "en"]), old_state,
                                                                 form_data=parsed_form_data)
        except WorkerUnknownError:
            return HTTPBadRequest()

    new_state = question.question_state
    webserver.state_storage.insert(webserver.package, json.loads(new_state))

    return web.json_response(new_state)


@routes.post('/repeat')
async def repeat_element(request: web.Request) -> web.Response:
    """Add Repetitions to the referenced RepetitionElement and store the form_data in the StateStorage."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    data = await request.json()
    old_form_data = add_repetition(form_data=parse_form_data(data['form_data']),
                                   reference=data['element-name'].replace(']', '').split('['),
                                   increment=int(data['increment']))
    stored_state = webserver.state_storage.get(webserver.package)
    old_state: Optional[bytes] = json.dumps(stored_state).encode() if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        manifest = await worker.get_manifest()
        try:
            question = await worker.create_question_from_options(RequestUser(["de", "en"]), old_state,
                                                                 form_data=old_form_data)
        except WorkerUnknownError:
            return HTTPBadRequest()

        new_state = question.question_state
        webserver.state_storage.insert(webserver.package, json.loads(new_state))
        form_definition: OptionsFormDefinition
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), new_state.encode())

    context = {
        'manifest': manifest,
        'options': form_definition.model_dump(),
        'form_data': form_data
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)
