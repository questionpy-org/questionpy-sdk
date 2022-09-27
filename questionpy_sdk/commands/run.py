import asyncio
import logging
from pathlib import Path

import click

from questionpy_server import WorkerPool

log = logging.getLogger(__name__)


@click.command()
@click.argument("package", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def run(package: Path) -> None:
    asyncio.run(run_worker(package))


async def run_worker(package: Path) -> None:
    worker_pool = WorkerPool(0, 0)
    async with worker_pool.get_worker(package, 0, 0) as worker:
        manifest = await worker.get_manifest()
        print(manifest)
        options = await worker.get_options_form_definition()
        print(options)
