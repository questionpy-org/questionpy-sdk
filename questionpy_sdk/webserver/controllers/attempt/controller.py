#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import random
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Literal, TypedDict, overload

import jinja2
from aiohttp import web

from questionpy import AttemptModel, AttemptScoredModel, AttemptStartedModel, ScoreModel
from questionpy_sdk.webserver.constants import DEFAULT_REQUEST_USER
from questionpy_sdk.webserver.controllers.base import BaseController

from .errors import RenderErrorCollections, log_render_errors
from .question_ui import QuestionDisplayOptions, QuestionFormulationUIRenderer, QuestionUIRenderer

if TYPE_CHECKING:
    from questionpy_server.worker import Worker


class AttemptStatus(StrEnum):
    STARTED = auto()
    IN_PROGRESS = auto()
    SCORED = auto()


class AttemptTemplateContext(TypedDict):
    formulation: str
    general_feedback: str | None
    specific_feedback: str | None
    right_answer: str | None


class AttemptRenderData(TypedDict):
    attempt_html: str
    attempt_status: AttemptStatus
    attempt_state: str
    render_errors: RenderErrorCollections
    variant: int
    scoring_state: str | None
    scoring_code: str | None
    score: float | None


class AttemptController(BaseController):
    async def get_attempt(self, display_options: QuestionDisplayOptions) -> AttemptRenderData:
        """Starts a new attempt or restores the previous attempt and renders the UI."""
        last_attempt_data = await self._get_last_attempt_data(allow_missing=True)
        attempt_state = await self._get_attempt_state(allow_missing=True)
        score = await self._get_score()

        attempt, attempt_state = await self._get_or_start_attempt(attempt_state, last_attempt_data, score)
        template_context, render_errors = await self._render_ui(attempt, display_options, last_attempt_data, score)

        log_render_errors(render_errors)

        data: AttemptRenderData = {
            "attempt_html": await self._attempt_template.render_async(template_context),
            "attempt_status": self._attempt_to_status(attempt),
            "attempt_state": attempt_state,
            "render_errors": render_errors,
            "variant": attempt.variant,
            "scoring_state": None,
            "scoring_code": None,
            "score": None,
        }

        if isinstance(attempt, AttemptScoredModel):
            data["scoring_state"] = attempt.scoring_state
            data["scoring_code"] = attempt.scoring_code.value
            data["score"] = attempt.score

        return data

    async def _get_or_start_attempt(
        self, attempt_state: str | None, last_attempt_data: dict, score: ScoreModel | None
    ) -> tuple[AttemptModel, str]:
        question_state = await self._get_question_state()
        worker: Worker

        # Display a previously started attempt...
        if attempt_state:
            async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
                attempt = await worker.get_attempt(
                    request_user=DEFAULT_REQUEST_USER,
                    question_state=question_state,
                    attempt_state=attempt_state,
                    scoring_state=score.scoring_state if score else None,
                    response=last_attempt_data,
                )

            if score:
                attempt = AttemptScoredModel(**attempt.model_dump(), **score.model_dump())

        # ...or start a new attempt.
        else:
            async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
                attempt = await worker.start_attempt(DEFAULT_REQUEST_USER, question_state, variant=1)
                attempt_state = attempt.attempt_state
                await self._state_manager.write_attempt_state(attempt_state)

        return attempt, attempt_state

    async def _render_ui(
        self,
        attempt: AttemptModel,
        display_options: QuestionDisplayOptions,
        last_attempt_data: dict,
        score: ScoreModel | None,
    ) -> tuple[AttemptTemplateContext, RenderErrorCollections]:
        # Force display options if not scored
        if not score:
            display_options.readonly = False
            display_options.general_feedback = display_options.specific_feedback = display_options.right_answer = False

        # Render UI
        renderer_args = (attempt.ui.placeholders, display_options, await self._get_attempt_seed(), last_attempt_data)
        html, errors = QuestionFormulationUIRenderer(attempt.ui.formulation, *renderer_args).render()

        template_context: AttemptTemplateContext = {
            "formulation": html,
            "general_feedback": None,
            "specific_feedback": None,
            "right_answer": None,
        }

        render_errors: RenderErrorCollections = {}
        if errors:
            render_errors["formulation"] = errors
        for key in ("general_feedback", "specific_feedback", "right_answer"):
            xml = getattr(attempt.ui, key)
            if getattr(display_options, key) and xml:
                html, errors = QuestionUIRenderer(xml, *renderer_args).render()
                template_context[key] = html
                if errors:
                    render_errors[key] = errors

        return template_context, render_errors

    @property
    def _attempt_template(self) -> jinja2.Template:
        loader = jinja2.PackageLoader("questionpy_sdk.webserver")
        jinja2_env = jinja2.Environment(loader=loader, autoescape=True, enable_async=True)
        return jinja2_env.get_template("attempt.html.jinja2")

    def _attempt_to_status(self, attempt: AttemptModel) -> AttemptStatus:
        return (
            AttemptStatus.STARTED
            if isinstance(attempt, AttemptStartedModel)
            else AttemptStatus.SCORED
            if isinstance(attempt, AttemptScoredModel)
            else AttemptStatus.IN_PROGRESS
        )

    async def save_attempt(self, data: Any) -> None:
        """Saves the attempt data."""
        await self._state_manager.write_last_attempt_data(data)

    async def reset_attempt(self) -> None:
        """Resets the attempt state."""
        await self._state_manager.delete_state()

    async def score_attempt(self) -> None:
        """Scores the attempt."""
        score = await self._get_score()

        worker: Worker
        async with self._worker_pool.get_worker(self._package_location, 0, None) as worker:
            attempt_scored = await worker.score_attempt(
                request_user=DEFAULT_REQUEST_USER,
                question_state=await self._get_question_state(),
                attempt_state=await self._get_attempt_state(),
                response=await self._get_last_attempt_data(),
                scoring_state=score.scoring_state if score else None,
            )

        await self._state_manager.write_score(attempt_scored)

    @overload
    async def _get_attempt_state(self, *, allow_missing: Literal[False] = ...) -> str: ...
    @overload
    async def _get_attempt_state(self, *, allow_missing: Literal[True]) -> str | None: ...

    async def _get_attempt_state(self, *, allow_missing: bool = False) -> str | None:
        try:
            return await self._state_manager.read_attempt_state()
        except FileNotFoundError as err:
            if allow_missing:
                return None
            raise web.HTTPConflict(text="No attempt state found") from err

    async def _get_attempt_seed(self) -> int:
        try:
            seed = await self._state_manager.read_attempt_seed()
        except FileNotFoundError:
            seed = random.randint(0, 1000)
            await self._state_manager.write_attempt_seed(seed)
        return seed

    async def _get_score(self) -> ScoreModel | None:
        try:
            return await self._state_manager.read_score()
        except FileNotFoundError:
            return None

    async def _get_last_attempt_data(self, *, allow_missing: bool = False) -> Any:
        try:
            return await self._state_manager.read_last_attempt_data()
        except FileNotFoundError as err:
            if allow_missing:
                return {}
            raise web.HTTPConflict(text="Last attempt data not found") from err
