from pathlib import Path
from jinja2 import FileSystemLoader
from aiohttp import web
import aiohttp_jinja2

from questionpy_common.constants import MiB
from questionpy_server import WorkerPool

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

    def start_server(self) -> None:
        web.run_app(self.web_app)


@routes.get('/')
async def render_options(_request: web.Request) -> web.Response:
    """Get the options form definition that allow a question creator to customize a question."""
    webserver: 'WebServer' = _request.app['sdk_webserver_app']

    async with webserver.worker_pool.get_worker(webserver.package, 0, None) as worker:
        manifest = await worker.get_manifest()
        options = await worker.get_options_form_definition()

    context = {
        'manifest': manifest,
        'options': options.dict()
    }

    return aiohttp_jinja2.render_template('options.html.jinja2', _request, context)
