#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
import random
from typing import TYPE_CHECKING

import aiohttp_jinja2
from aiohttp import web
from pydantic import TypeAdapter

from questionpy_common.api.attempt import AttemptScoredModel, ScoreModel
from questionpy_common.environment import RequestUser
from questionpy_sdk.webserver.app import SDK_WEBSERVER_APP_KEY
from questionpy_sdk.webserver.attempt import get_attempt_render_context
from questionpy_sdk.webserver.question_ui import QuestionDisplayOptions

if TYPE_CHECKING:
    from questionpy_server.worker.worker import Worker

routes = web.RouteTableDef()


def set_cookie(
    response: web.Response, name: str, value: str, max_age: int | None = 3600, same_site: str | None = "Strict"
) -> None:
    response.set_cookie(name=name, value=value, max_age=max_age, samesite=same_site)


@routes.get("/attempt")
async def get_attempt(request: web.Request) -> web.Response:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]
    stored_state = webserver.state_storage.get(webserver.package_location)
    if not stored_state:
        return web.HTTPNotFound(reason="No question state found.")
    question_state = json.dumps(stored_state)

    display_options = QuestionDisplayOptions.model_validate_json(request.cookies.get("display_options", "{}"))

    seed = int(request.cookies["attempt_seed"]) if "attempt_seed" in request.cookies else random.randint(0, 10)

    attempt_state = request.cookies.get("attempt_state")
    score_json = request.cookies.get("score")
    last_attempt_data = json.loads(request.cookies.get("last_attempt_data", "{}"))

    score = None
    if score_json:
        score = ScoreModel.model_validate_json(score_json)

    worker: Worker
    if attempt_state:
        # Display a previously started attempt.
        async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
            attempt = await worker.get_attempt(
                request_user=RequestUser(["de", "en"]),
                question_state=question_state,
                attempt_state=attempt_state,
                scoring_state=score.scoring_state if score else None,
                response=last_attempt_data,
            )

        if score:
            attempt = AttemptScoredModel(**attempt.model_dump(), **score.model_dump())
    else:
        # Start a new attempt.
        async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
            attempt = await worker.start_attempt(
                request_user=RequestUser(["de", "en"]), question_state=question_state, variant=1
            )
            attempt_state = attempt.attempt_state

    if not score:
        # TODO: Allow manually set display options to override this.
        display_options.readonly = False
        display_options.general_feedback = display_options.feedback = display_options.right_answer = False

    context = get_attempt_render_context(
        attempt,
        attempt_state,
        last_attempt_data=last_attempt_data,
        display_options=display_options,
        seed=seed,
        disabled=score is not None,
    )

    response = aiohttp_jinja2.render_template("attempt.html.jinja2", request, context)
    set_cookie(response, "attempt_state", attempt_state)
    set_cookie(response, "attempt_seed", str(seed))
    return response


async def _score_attempt(request: web.Request, data: dict) -> web.Response:
    webserver = request.app[SDK_WEBSERVER_APP_KEY]

    stored_state = webserver.state_storage.get(webserver.package_location)
    if not stored_state:
        return web.HTTPNotFound(reason="No question state found.")
    question_state = json.dumps(stored_state)

    display_options = QuestionDisplayOptions.model_validate_json(request.cookies.get("display_options", "{}"))
    display_options.readonly = True

    attempt_state = request.cookies.get("attempt_state")
    if not attempt_state:
        return web.HTTPNotFound(reason="Attempt has to be started before being submitted. Try reloading the page.")

    score_json = request.cookies.get("score")
    score = ScoreModel.model_validate_json(score_json) if score_json else None

    worker: Worker
    async with webserver.worker_pool.get_worker(webserver.package_location, 0, None) as worker:
        attempt_scored = await worker.score_attempt(
            request_user=RequestUser(["de", "en"]),
            question_state=question_state,
            attempt_state=attempt_state,
            response=data,
            scoring_state=score.scoring_state if score else None,
        )

    response = web.Response(status=201)
    set_cookie(response, "display_options", display_options.model_dump_json())
    set_cookie(response, "score", TypeAdapter(ScoreModel).dump_json(attempt_scored).decode())
    return response


@routes.post("/attempt")
async def submit_attempt(request: web.Request) -> web.Response:
    data = await request.json()
    response = await _score_attempt(request, data)
    set_cookie(response, "last_attempt_data", json.dumps(data))
    return response


@routes.post("/attempt/rescore")
async def rescore_attempt(request: web.Request) -> web.Response:
    data_json = request.cookies.get("last_attempt_data")
    data = json.loads(data_json) if data_json else None
    return await _score_attempt(request, data)


@routes.post("/attempt/display-options")
async def submit_display_options(request: web.Request) -> web.Response:
    data = await request.json()
    display_options_dict = json.loads(request.cookies.get("display_options", "{}"))
    display_options_dict.update(data)
    display_options = QuestionDisplayOptions.model_validate(display_options_dict)

    response = web.Response(status=201)
    set_cookie(response, "display_options", display_options.model_dump_json())
    return response


@routes.post("/attempt/restart")
async def restart_attempt(request: web.Request) -> web.Response:
    """Restarts the attempt by deleting the attempt scored state and last attempt data and by resetting the seed."""
    response = web.Response(status=201)
    response.del_cookie("attempt_state")
    response.del_cookie("score")
    response.del_cookie("last_attempt_data")
    response.del_cookie("attempt_seed")
    return response


@routes.post("/attempt/edit")
async def edit_last_attempt(request: web.Request) -> web.Response:
    """Removes the attempt scored state."""
    response = web.Response(status=201)
    response.del_cookie("score")
    return response


@routes.post("/attempt/save")
async def save_attempt(request: web.Request) -> web.Response:
    last_attempt_data = await request.json()
    response = web.Response(status=201)
    set_cookie(response, "last_attempt_data", json.dumps(last_attempt_data))
    return response
