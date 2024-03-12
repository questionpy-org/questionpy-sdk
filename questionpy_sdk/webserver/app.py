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
from questionpy_common.api.attempt import AttemptScoredModel
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


def set_cookie(response: web.Response, name: str, value: str, max_age: Optional[int] = 3600,
               same_site: Optional[str] = 'Strict') -> None:
    response.set_cookie(name=name, value=value, max_age=max_age, samesite=same_site)


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

        self.attempt_state: Optional[str] = None
        self.attempt_started: Optional[AttemptStarted] = None
        self.attempt_scored: Optional[AttemptScoredModel] = None
        self.last_attempt_data: Optional[dict] = None
        self.attempt_seed: int = -1

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
        except WorkerUnknownError as exc:
            raise HTTPBadRequest() from exc

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
        except WorkerUnknownError as exc:
            raise HTTPBadRequest() from exc

        new_state = question.question_state
        webserver.state_storage.insert(webserver.package_location, json.loads(new_state))
        form_definition: OptionsFormDefinition
        form_definition, form_data = await worker.get_options_form(RequestUser(["de", "en"]), new_state)

    context = {
        'manifest': manifest,
        'options': contextualize(form_definition=form_definition, form_data=form_data).model_dump()
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


async def get_attempt_started_context(webserver: WebServer, question_state: str,
                                      display_options: QuestionDisplayOptions) -> dict:
    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        try:
            webserver.attempt_started = await worker.start_attempt(RequestUser(["de", "en"]), question_state, 1)
        except WorkerUnknownError as exc:
            raise HTTPBadRequest() from exc

    renderer = QuestionUIRenderer(xml=webserver.attempt_started.ui.content,
                                  placeholders=webserver.attempt_started.ui.placeholders,
                                  seed=webserver.attempt_seed)
    return {
        'question_html': renderer.render_formulation(
            attempt=webserver.last_attempt_data,
            options=QuestionDisplayOptions(general_feedback=False, feedback=False)),
        'options': display_options.model_dump(exclude={'context', 'readonly'}),
        'form_disabled': False
    }


async def get_attempt_scored_context(webserver: WebServer, display_options: QuestionDisplayOptions) -> dict:
    assert webserver.attempt_scored
    renderer = QuestionUIRenderer(xml=webserver.attempt_scored.ui.content,
                                  placeholders=webserver.attempt_scored.ui.placeholders,
                                  seed=webserver.attempt_seed)
    context = {
        'question_html': renderer.render_formulation(attempt=webserver.last_attempt_data,
                                                     options=display_options),
        'options': display_options.model_dump(exclude={'context', 'readonly'}),
        'form_disabled': True
    }

    if display_options.general_feedback:
        context['general_feedback'] = renderer.render_general_feedback(attempt=webserver.last_attempt_data,
                                                                       options=display_options)
    if display_options.feedback:
        context['specific_feedback'] = renderer.render_specific_feedback(attempt=webserver.last_attempt_data,
                                                                         options=display_options)
    if display_options.right_answer:
        context['right_answer'] = renderer.render_right_answer(attempt=webserver.last_attempt_data,
                                                               options=display_options)
    return context


@routes.get('/attempt')
async def get_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    question_state = json.dumps(stored_state) if stored_state else None
    display_options = QuestionDisplayOptions(**json.loads(request.cookies.get('display_options', '{}')))
    attempt_started_dict = json.loads(request.cookies.get('attempt_started', '{}'))
    attempt_scored_dict = json.loads(request.cookies.get('attempt_scored', '{}'))
    webserver.last_attempt_data = json.loads(request.cookies.get('last_attempt_data', '{}'))
    webserver.attempt_seed = int(request.cookies.get('attempt_seed', -1))

    if not question_state:
        return web.HTTPNotFound(reason="No question state found.")

    if webserver.attempt_seed < 0:
        webserver.attempt_seed = random.randint(0, 10)

    if attempt_started_dict and attempt_scored_dict:
        webserver.attempt_started = AttemptStarted(**attempt_started_dict)
        webserver.attempt_scored = AttemptScoredModel(**attempt_scored_dict)
        context = await get_attempt_scored_context(webserver, display_options)
    else:
        context = await get_attempt_started_context(webserver, question_state, display_options)
        assert webserver.attempt_started

    response = aiohttp_jinja2.render_template('attempt.html.jinja2', request, context)
    set_cookie(response, 'attempt_started', webserver.attempt_started.model_dump_json())
    set_cookie(response, 'attempt_seed', str(webserver.attempt_seed))
    return response


@routes.post('/attempt')
async def submit_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    if not stored_state:
        return web.HTTPNotFound(reason="No question state found.")

    question_state = json.dumps(stored_state)

    display_options = QuestionDisplayOptions(**json.loads(request.cookies.get('display_options', '{}')))
    display_options.readonly = True

    webserver.last_attempt_data = await request.json()

    if not webserver.attempt_started:
        return web.HTTPNotFound(reason="Attempt has to be started before being submitted. Try reloading the page.")

    if not webserver.last_attempt_data:
        return web.HTTPBadRequest()

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        webserver.attempt_scored = await worker.score_attempt(
            request_user=RequestUser(["de", "en"]),
            question_state=question_state, attempt_state=webserver.attempt_started.attempt_state,
            response=webserver.last_attempt_data,
        )

    response = web.json_response(status=201, text='Attempt submitted.')
    set_cookie(response, 'display_options', display_options.model_dump_json())
    set_cookie(response, 'attempt_scored', webserver.attempt_scored.model_dump_json())
    set_cookie(response, 'last_attempt_data', json.dumps(webserver.last_attempt_data))
    return response


@routes.post('/attempt/display-options')
async def submit_display_options(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        display_options_dict = json.loads(request.cookies.get('display_options', '{}'))
        display_options_dict.update(data)
        display_options = QuestionDisplayOptions(**display_options_dict)
        response = web.json_response(status=201, text='Options updated.')
        set_cookie(response, 'display_options', display_options.model_dump_json())
        return response
    except Exception as e:
        raise web.HTTPBadRequest() from e


@routes.post('/attempt/restart')
async def restart_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    webserver.attempt_scored = None
    webserver.last_attempt_data = None
    webserver.attempt_seed = random.randint(0, 10)

    response = web.json_response(status=201, text='Attempt restarted.')
    response.del_cookie('attempt_scored')
    response.del_cookie('last_attempt_data')
    set_cookie(response, 'attempt_seed', str(webserver.attempt_seed))
    return response


@routes.post('/attempt/edit')
async def edit_last_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    webserver.attempt_scored = None

    response = web.json_response(status=201, text='Attempt restarted.')
    response.del_cookie('attempt_scored')
    return response
