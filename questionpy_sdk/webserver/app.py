from pathlib import Path
import os
from jinja2 import FileSystemLoader
from aiohttp import web
import aiohttp_jinja2

from questionpy_common.constants import MiB
from questionpy_server import WorkerPool
from questionpy_sdk.webserver import parser

routes = web.RouteTableDef()


class WebServer:

    def __init__(self, package: Path):
        self.web_app = web.Application()
        routes.static('/static', os.path.join(os.path.dirname(__file__), 'static'))
        self.web_app.add_routes(routes)
        self.web_app['sdk_webserver_app'] = self

        template_folder = os.path.join(os.path.dirname(__file__), 'templates')
        jinja2_extensions = ['jinja2.ext.do']
        aiohttp_jinja2.setup(self.web_app,
                             loader=FileSystemLoader(template_folder),
                             extensions=jinja2_extensions)
        self.worker_pool = WorkerPool(1, 500 * MiB)
        self.package = package

    def start_server(self) -> None:
        web.run_app(self.web_app)


@routes.get('/')
async def render_options(_request: web.Request) -> web.Response:
    webserver: 'WebServer' = _request.app['sdk_webserver_app']

    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        manifest = await worker.get_manifest()
        options = await worker.get_options_form_definition()

    context = {
        'layout': 'options.html',
        'manifest': manifest,
        'options': parser.to_dict(options)
    }
    return aiohttp_jinja2.render_template('options.html', _request, context)
