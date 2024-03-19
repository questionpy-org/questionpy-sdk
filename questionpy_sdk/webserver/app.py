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
from questionpy_server.worker.runtime.package_location import PackageLocation
from questionpy_server.worker.runtime.messages import WorkerUnknownError
from questionpy_server.worker.worker import Worker
from questionpy_server.worker.worker.thread import ThreadWorker

from questionpy_sdk.webserver.attempt import get_attempt_scored_context, get_attempt_started_context
from questionpy_sdk.webserver.context import contextualize
from questionpy_sdk.webserver.question_ui import QuestionDisplayOptions
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


@routes.get('/attempt')
async def get_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    if not stored_state:
        return web.HTTPNotFound(reason="No question state found.")
    question_state = json.dumps(stored_state)

    display_options = QuestionDisplayOptions.model_validate_json(request.cookies.get('display_options', '{}'))
    seed = int(request.cookies.get('attempt_seed', -1))

    if seed < 0:
        seed = random.randint(0, 10)

    attempt_state = request.cookies.get('attempt_state')
    scoring_state = request.cookies.get('scoring_state')
    last_attempt_data = json.loads(request.cookies.get('last_attempt_data', '{}'))

    worker: Worker
    if attempt_state:
        async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
            try:
                attempt = await worker.get_attempt(request_user=RequestUser(["de", "en"]),
                                                   question_state=question_state,
                                                   attempt_state=attempt_state,
                                                   scoring_state=scoring_state,
                                                   response=last_attempt_data)
            except WorkerUnknownError as exc:
                raise HTTPBadRequest() from exc

        if scoring_state:
            context = get_attempt_scored_context(attempt.ui, last_attempt_data, display_options, seed)
        else:
            context = get_attempt_started_context(attempt.ui, last_attempt_data, display_options, seed)

    else:
        async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
            try:
                attempt_started = await worker.start_attempt(request_user=RequestUser(["de", "en"]),
                                                             question_state=question_state,
                                                             variant=1)
            except WorkerUnknownError as exc:
                raise HTTPBadRequest() from exc
        attempt_state = attempt_started.attempt_state
        context = get_attempt_started_context(attempt_started.ui, last_attempt_data, display_options, seed)

    response = aiohttp_jinja2.render_template('attempt.html.jinja2', request, context)
    set_cookie(response, 'attempt_state', attempt_state)
    set_cookie(response, 'attempt_seed', str(seed))
    return response


@routes.post('/attempt')
async def submit_attempt(request: web.Request) -> web.Response:
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    stored_state = webserver.state_storage.get(webserver.package_location)
    if not stored_state:
        return web.HTTPNotFound(reason="No question state found.")

    question_state = json.dumps(stored_state)

    display_options = QuestionDisplayOptions.model_validate_json(request.cookies.get('display_options', '{}'))
    display_options.readonly = True

    attempt_state = request.cookies.get('attempt_state')
    if not attempt_state:
        return web.HTTPNotFound(reason="Attempt has to be started before being submitted. Try reloading the page.")

    last_attempt_data = await request.json()
    if not last_attempt_data:
        return web.HTTPBadRequest()

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        attempt_scored = await worker.score_attempt(
            request_user=RequestUser(["de", "en"]),
            question_state=question_state, attempt_state=attempt_state,
            response=last_attempt_data,
        )

    response = web.Response(status=201)
    set_cookie(response, 'display_options', display_options.model_dump_json())
    set_cookie(response, 'scoring_state', attempt_scored.scoring_state)
    set_cookie(response, 'last_attempt_data', json.dumps(last_attempt_data))
    return response


@routes.post('/attempt/display-options')
async def submit_display_options(request: web.Request) -> web.Response:
    data = await request.json()
    display_options_dict = json.loads(request.cookies.get('display_options', '{}'))
    display_options_dict.update(data)
    display_options = QuestionDisplayOptions.model_validate(display_options_dict)

    response = web.Response(status=201)
    set_cookie(response, 'display_options', display_options.model_dump_json())
    return response


@routes.post('/attempt/restart')
async def restart_attempt(request: web.Request) -> web.Response:
    """Restarts the attempt by deleting the attempt scored state and last attempt data and by resetting the seed."""
    response = web.Response(status=201)
    response.del_cookie('scoring_state')
    response.del_cookie('last_attempt_data')
    set_cookie(response, 'attempt_seed', str(random.randint(0, 10)))
    return response


@routes.post('/attempt/edit')
async def edit_last_attempt(request: web.Request) -> web.Response:
    """Removes the attempt scored state."""
    response = web.Response(status=201)
    response.del_cookie('scoring_state')
    return response


@routes.post('/attempt/save')
async def save_attempt(request: web.Request) -> web.Response:
    last_attempt_data = await request.json()
    if not last_attempt_data:
        return web.HTTPBadRequest()

    response = web.Response(status=201)
    set_cookie(response, 'last_attempt_data', json.dumps(last_attempt_data))
    return response
