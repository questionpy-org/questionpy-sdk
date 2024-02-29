#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
import random
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
from questionpy_server.api.models import AttemptStarted
from questionpy_server.worker.runtime.package_location import PackageLocation
from questionpy_server.worker.runtime.messages import WorkerUnknownError
from questionpy_server.worker.worker import Worker
from questionpy_server.worker.worker.thread import ThreadWorker

from questionpy_sdk.webserver.context import contextualize
from questionpy_sdk.webserver.question_ui import QuestionUIRenderer, QuestionDisplayOptions
from questionpy_sdk.webserver.state_storage import QuestionStateStorage, add_repetition, parse_form_data

routes = web.RouteTableDef()


class WebServer:
    def __init__(self, package_location: PackageLocation,
                 state_storage_path: Path = Path(__file__).parent / 'question_state_storage'):
        self.package_location = package_location
        self.state_storage = QuestionStateStorage(state_storage_path)

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

        self.attempt_state = None
        self.attempt_started = None
        self.attempt_scored = None
        self.attempt_seed = random.randint(0, 10)
        self.display_options = QuestionDisplayOptions(general_feedback=True, feedback=True)

    def start_server(self) -> None:
        web.run_app(self.web_app)


@routes.get('/')
async def render_options(request: web.Request) -> web.Response:
    """Get the options form definition that allows a question creator to customize a question."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), old_state)

    context = {
        'manifest': manifest,
        'options': contextualize(form_definition=form_definition, form_data=form_data).model_dump()
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


@routes.post('/submit')
async def submit_form(request: web.Request) -> web.Response:
    """Store the form_data from the Options Form in the StateStorage."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    data = await request.json()
    parsed_form_data = parse_form_data(data)
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        try:
            question = await worker.create_question_from_options(RequestUser(["de", "en"]), old_state,
                                                                 form_data=parsed_form_data)
        except WorkerUnknownError:
            raise HTTPBadRequest()

    new_state = question.question_state
    webserver.state_storage.insert(webserver.package_location, json.loads(new_state))

    return web.json_response(new_state)


@routes.post('/repeat')
async def repeat_element(request: web.Request) -> web.Response:
    """Add Repetitions to the referenced RepetitionElement and store the form_data in the StateStorage."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    data = await request.json()
    old_form_data = add_repetition(form_data=parse_form_data(data['form_data']),
                                   reference=data['element-name'].replace(']', '').split('['),
                                   increment=int(data['increment']))
    stored_state = webserver.state_storage.get(webserver.package_location)
    old_state = json.dumps(stored_state) if stored_state else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        manifest = await worker.get_manifest()
        try:
            question = await worker.create_question_from_options(RequestUser(["de", "en"]), old_state,
                                                                 form_data=old_form_data)
        except WorkerUnknownError:
            raise HTTPBadRequest()

        new_state = question.question_state
        webserver.state_storage.insert(webserver.package_location, json.loads(new_state))
        form_definition: OptionsFormDefinition
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), new_state)

    context = {
        'manifest': manifest,
        'options': contextualize(form_definition=form_definition, form_data=form_data).model_dump()
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


async def started_attempt(webserver: WebServer, question_state: str) -> dict:
    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        try:
            webserver.attempt_started = await worker.start_attempt(RequestUser(["de", "en"]), question_state, 1)
        except WorkerUnknownError:
            raise HTTPBadRequest()

    renderer = QuestionUIRenderer(xml=webserver.attempt_started.ui.content,
                                  placeholders=webserver.attempt_started.ui.placeholders,
                                  seed=webserver.attempt_seed)
    return {
        'question_html': renderer.render_formulation(
            options=QuestionDisplayOptions(general_feedback=False, feedback=False)),
        'options': webserver.display_options.model_dump(exclude={'context', 'readonly'}),
        'form_disabled': False
    }


async def scored_attempt(webserver: WebServer) -> dict:
    renderer = QuestionUIRenderer(xml=webserver.attempt_scored.ui.content,
                                  placeholders=webserver.attempt_scored.ui.placeholders,
                                  seed=webserver.attempt_seed)
    return {
        'question_html': renderer.render_formulation(options=webserver.display_options),
        'options': webserver.display_options.model_dump(exclude={'context', 'readonly'}),
        'form_disabled': True
    }


@routes.get('/attempt')
async def get_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    question_state = json.dumps(stored_state) if stored_state else None

    if not question_state:
        return web.HTTPNotFound()

    if webserver.attempt_started and webserver.attempt_scored:
        context = await scored_attempt(webserver)
    else:
        context = await started_attempt(webserver, question_state)

    return aiohttp_jinja2.render_template('attempt.html.jinja2', request, context)


@routes.post('/attempt')
async def submit_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    question_state = json.dumps(stored_state) if stored_state else None

    webserver.display_options.readonly = True

    data = await request.json()

    if not webserver.attempt_started:
        return web.HTTPNotFound()

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        webserver.attempt_scored = await worker.score_attempt(
            request_user=RequestUser(["de", "en"]),
            question_state=question_state, attempt_state=webserver.attempt_started.attempt_state,
            response=data,
        )

    return web.json_response(status=201, text='Attempt submitted.')


@routes.post('/attempt/display-options')
async def submit_display_options(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    try:
        data = await request.json()
        display_options_dict = webserver.display_options.model_dump()
        display_options_dict.update(data)
        webserver.display_options = QuestionDisplayOptions(**display_options_dict)
    except Exception as e:
        raise web.HTTPBadRequest() from e

    return web.json_response(status=201, text='Options updated.')
