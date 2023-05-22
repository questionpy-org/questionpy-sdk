import json
from pathlib import Path

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
from jinja2 import FileSystemLoader
from questionpy_common.constants import MiB
from questionpy_server import WorkerPool
from questionpy_server.worker.exception import WorkerUnknownError

from questionpy_sdk.webserver.state_storage import QuestionStateStorage

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
        self.worker_pool = WorkerPool(1, 500 * MiB)
        self.package = package
        self.state_storage = QuestionStateStorage()

    def start_server(self) -> None:
        web.run_app(self.web_app)


@routes.get('/')
async def render_options(request: web.Request) -> web.Response:
    """Get the options form definition that allow a question creator to customize a question."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']

    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        manifest = await worker.get_manifest()
        form_definition, _ = await worker.get_options_form(None)

    context = {
        'manifest': manifest,
        'options': form_definition.dict(),
        'form_data': webserver.state_storage.get(webserver.package)
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


@routes.post('/submit')
async def submit_form(request: web.Request) -> web.Response:
    """Get the options form definition and the form data on."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    form_data = await request.json()
    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        form_definition, _ = await worker.get_options_form(None)
        options = webserver.state_storage.parse_form_data(form_definition, form_data)
        try:
            question = await worker.create_question_from_options(old_state=None, form_data=options)
        except WorkerUnknownError:
            return HTTPBadRequest()

    question_state = json.loads(question.question_state)
    webserver.state_storage.insert(webserver.package, question_state)

    return web.json_response(form_data)
