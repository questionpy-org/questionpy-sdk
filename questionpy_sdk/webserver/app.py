from pathlib import Path

import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader
from questionpy_common.constants import MiB
from questionpy_server import WorkerPool

from questionpy_sdk.webserver.form_storage import FormStorage

routes = web.RouteTableDef()


class WebServer:

    def __init__(self, package: Path):
        self.web_app = web.Application()
        webserver_path = Path(__file__).parent
        routes.static('/static', webserver_path / 'static')
        self.web_app.add_routes(routes)
        self.web_app['sdk_webserver_app'] = self

        template_folder = webserver_path / 'templates'
        jinja2_extensions = ['jinja2.ext.do']
        aiohttp_jinja2.setup(self.web_app,
                             loader=FileSystemLoader(template_folder),
                             extensions=jinja2_extensions)
        self.worker_pool = WorkerPool(1, 500 * MiB)
        self.package = package
        self.form_storage = FormStorage()

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
        'form_data': webserver.form_storage.get(webserver.package)
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', request, context)


@routes.post('/submit')
async def submit_form(request: web.Request) -> web.Response:
    """Get the options form definition and the form data on."""
    webserver: 'WebServer' = request.app['sdk_webserver_app']
    form_data = await request.json()
    webserver.form_storage.insert(webserver.package, form_data)

    return web.json_response(form_data)
